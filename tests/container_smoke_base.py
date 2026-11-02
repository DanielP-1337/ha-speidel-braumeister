"""Synthetic ARM64 baseline check. Internal network, no host mounts or real endpoints."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

CLOUD = r'''
from aiohttp import web
import gzip,zlib
async def reply(r):
    body=await r.read()
    mode=r.path.rsplit('/',1)[-1]
    headers={'Content-Type':'application/octet-stream','X-Probe':'not-forwarded'}
    if mode=='drop':
        r.transport.close();return web.Response()
    if mode=='gzip':body=gzip.compress(body);headers['Content-Encoding']='gzip'
    if mode=='deflate':body=zlib.compress(body);headers['Content-Encoding']='deflate'
    if mode=='raw':body=zlib.compress(body)[2:-4];headers['Content-Encoding']='deflate'
    if mode=='stacked':body=zlib.compress(gzip.compress(body));headers['Content-Encoding']='gzip, deflate'
    if mode=='badgzip':body=b'bad';headers['Content-Encoding']='gzip'
    assert r.headers['Accept-Encoding']=='identity'
    return web.Response(status=503 if mode=='error' else 200,body=body,headers=headers)
app=web.Application();app.router.add_route('*','/{tail:.*}',reply)
web.run_app(app,port=8080,access_log=None)
'''

BOOT = r'''
import json,os,sys
from pathlib import Path
options={'bridge_ip':'127.0.0.1','cloud_host':'synthetic.invalid','forward_to_cloud':True,
 'upstream_dns':'127.0.0.1','dns_port':0,'cloud_dns':['1.1.1.1','1.0.0.1'],
 'http_port':80,'passthrough_url':'','api_port':8642,'log_level':'error',
 'cloud_url':'http://cloud:8080','api_host':'0.0.0.0'}
Path('/data/options.json').write_text(json.dumps(options))
os.execv(sys.executable,[sys.executable,'/app/bridge.py'])
'''

DRIVER = r'''
import json,platform,time,urllib.request,urllib.error
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(path,data=None):
    req=urllib.request.Request('http://bridge:'+('8642' if path.startswith('/api/') else '80')+path,
        data=data,headers={'Host':'synthetic.invalid','Content-Type':'application/octet-stream'})
    try:
        with op.open(req,timeout=12) as r:return r.status,dict(r.headers),r.read()
    except urllib.error.HTTPError as r:return r.code,dict(r.headers),r.read()
for _ in range(100):
    try:
        health=json.loads(get('/api/health')[2]);break
    except Exception:time.sleep(.1)
else:raise AssertionError('startup failed')
assert 'diagnostics' not in health
payload=b'opaque\x00\xff'+bytes(range(256))
local=b'Start\r\nOK\r\nDone\r\n'
for mode in ('plain','gzip','deflate','raw','empty','error','badgzip','stacked','drop'):
    sent=b'' if mode=='empty' else payload
    status,headers,body=get('/case/'+mode,sent)
    assert status==(503 if mode=='error' else 200),(mode,status)
    assert body==(local if mode in ('badgzip','stacked','drop') else sent),mode
    assert 'Content-Encoding' not in headers and 'X-Probe' not in headers
rz=b'rz=V1.1.27;SYNTHETIC;1793600000;1\r\nsynthetic-recipe;0;0'
get('/case/plain',rz)
d=json.loads(get('/api/status')[2])['devices'][0]
assert d['last_response_source']=='cloud' and 'synthetic-recipe' in d['rz']
get('/case/drop',rz)
assert json.loads(get('/api/status')[2])['devices'][0]['last_response_source']=='local'
print(json.dumps({'runtime':platform.machine(),'exchanges':11,'binary_and_compression':True,
 'cloud_and_fallback':True,'stacked_encoding_falls_back':True,'extra_response_headers_removed':True}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    args = parser.parse_args()
    label = 'bm-base-' + uuid.uuid4().hex[:12]
    owned = []
    network = volume = None

    def docker(*args):
        p = subprocess.run(['docker', '--context', 'desktop-linux', *args], capture_output=True, text=True, timeout=180)
        if p.returncode:
            raise RuntimeError(p.stderr)
        return (p.stdout + (p.stderr if args[0] == 'logs' else '')).strip()

    try:
        info = json.loads(docker('image', 'inspect', args.image))[0]
        assert info['Architecture'] == 'arm64'
        network = docker('network', 'create', '--internal', '--label', 'codex.braumeister.base='+label, label)
        assert json.loads(docker('network', 'inspect', network))[0]['Internal']
        volume = docker('volume', 'create', '--label', 'codex.braumeister.base='+label, label)
        with tempfile.TemporaryDirectory(prefix=label) as td:
            def create(role, code, *extra):
                cid = docker('create', '--platform', 'linux/arm64', '--network', network, '--network-alias', role,
                             '--label', 'codex.braumeister.base='+label, '--entrypoint', 'python3',
                             *extra, args.image, '/smoke.py')
                owned.append(cid)
                path = Path(td) / (role+'.py')
                path.write_text(code)
                docker('cp', str(path), cid+':/smoke.py')
                docker('start', cid)
                return cid
            create('cloud', CLOUD)
            bridge = create('bridge', BOOT, '--mount', 'type=volume,src='+volume+',dst=/data')
            driver = create('driver', DRIVER)
            result = docker('wait', driver)
            logs = docker('logs', driver)
            assert result == '0', logs
            print(logs, flush=True)
            check = "import hashlib,json;from pathlib import Path;print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/app').glob('*.py')}))"
            inside = json.loads(docker('exec', bridge, 'python3', '-c', check))
            source = Path(__file__).resolve().parents[1]/'braumeister_bridge/app/bridge.py'
            # Git checkout may use CRLF. The tested build must equal this checkout.
            assert inside == {'bridge.py':hashlib.sha256(source.read_bytes()).hexdigest()}
            docker('restart', bridge)
            check = '''
import json,time,urllib.request
from pathlib import Path
for attempt in range(200):
    try:
        d=json.load(urllib.request.urlopen('http://127.0.0.1:8642/api/status',timeout=2));break
    except OSError:time.sleep(.1)
else:raise AssertionError('restart did not become ready')
assert 'synthetic-recipe' in d['devices'][0]['rz']
assert not Path('/data/diagnostics').exists()
assert json.loads(Path('/data/options.json').read_text())['dns_port']==0
print('restart_recipes_retained=true recorder_absent=true')
'''
            print(docker('exec', bridge, 'python3', '-c', check), flush=True)
            print(json.dumps({'image_id':info['Id'],'architecture':info['Architecture'],'source_hashes':inside,'internal_network':True}), flush=True)
    finally:
        for cid in reversed(owned):
            docker('rm', '--force', cid)
        if volume:
            docker('volume', 'rm', volume)
        if network:
            docker('network', 'rm', network)
        print('owned_resources_removed=true', flush=True)


if __name__ == '__main__':
    main()
