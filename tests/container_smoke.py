"""Run the built add-on on an internal-only disposable Docker network.

No published ports, bind mounts, Docker socket, external runtime fetches or real
endpoints. Build/pull separately. Only IDs created by this invocation are removed.
Usage: python tests/container_smoke.py --image IMAGE --platform linux/arm64
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import tarfile
import uuid

CLOUD = r'''
from aiohttp import web
import gzip, json, zlib
seen=[]
async def reply(r):
    data=await r.read()
    if r.path == '/seen': return web.json_response(seen)
    seen.append([r.method,r.path_qs,data.hex(),r.headers.get('Authorization'),r.headers.get('Accept-Encoding')])
    mode=r.path.rsplit('/',1)[-1]
    body=b'Start\r\n$unknown=one\r\n$unknown=two\r\n'+bytes(range(256))+b'\r\nOK\r\nDone\r\n'
    if mode=='large': return web.Response(body=b'\x00'*(2*1024*1024))
    if mode=='empty': return web.Response(body=b'')
    if mode=='error': return web.Response(status=503,body=b'synthetic cloud error')
    if mode=='drop':
        r.transport.close()
        return web.Response()
    if mode=='badgzip': return web.Response(body=b'invalid gzip',headers={'Content-Encoding':'gzip'})
    if mode=='gzip': return web.Response(body=gzip.compress(body),headers={'Content-Encoding':'gzip'})
    if mode=='deflate': return web.Response(body=zlib.compress(body),headers={'Content-Encoding':'deflate'})
    if mode=='raw': return web.Response(body=zlib.compress(body)[2:-4],headers={'Content-Encoding':'deflate'})
    return web.Response(body=body)
app=web.Application();app.router.add_route('*','/{tail:.*}',reply)
web.run_app(app,port=8080,access_log=None)
'''

BOOT = r'''
import json, os, sys
from pathlib import Path
mode=os.environ['SMOKE_MODE']
options={'bridge_ip':'127.0.0.1','upstream_dns':'127.0.0.1','cloud_host':'device.test.invalid','cloud_url':'http://cloud:8080','cloud_dns':[],
 'forward_to_cloud':True,'dns_port':0,'http_port':80,'api_port':8642,'api_host':'0.0.0.0',
 'state_file':'','log_level':'error','diagnostics_enabled':mode not in ('off','baseline'),
 'diagnostics_max_file_mb':8,'diagnostics_files':4}
if mode=='fault':
 Path('/data/blocked').write_text('synthetic unavailable directory')
 options['diagnostics_directory']='/data/blocked'
Path('/data/options.json').write_text(json.dumps(options))
Path('/data/prior-state.bin').write_bytes(b'synthetic persistent state\x00\xff')
os.execv(sys.executable,[sys.executable,'/app/bridge.py'])
'''

DRIVER = r'''
import hashlib,json,platform,sys,time,urllib.request,urllib.error
hosts=json.loads(sys.argv[1]);opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
def get(url,data=None,method=None,timeout=12):
 req=urllib.request.Request(url,data=data,method=method,
  headers={'Host':'device.test.invalid','Authorization':'Basic c3ludGhldGljOnRlc3Q=',
           'Cookie':'synthetic-cookie','Content-Type':'application/octet-stream'})
 try:
  with opener.open(req,timeout=timeout) as r:return r.status,dict(r.headers),r.read()
 except urllib.error.HTTPError as r:return r.code,dict(r.headers),r.read()
for host in hosts.values():
 deadline=time.monotonic()+45
 while time.monotonic()<deadline:
  try:get('http://'+host+':8642/api/health',timeout=2);break
  except Exception:time.sleep(.2)
 else:raise AssertionError('bridge did not start: '+host)
expected=b'Start\r\n$unknown=one\r\n$unknown=two\r\n'+bytes(range(256))+b'\r\nOK\r\nDone\r\n'
local=b'Start\r\nOK\r\nDone\r\n';modes=['plain','gzip','deflate','raw','empty','error','badgzip','drop','large']
results={}
for name,host in hosts.items():
 results[name]=[]
 for mode in modes:
  status,headers,body=get('http://'+host+'/case/'+mode+'?q=same%2Ftest',b'opaque\x00\xff','PUT')
  target=local if mode in ('drop','badgzip') else (b'' if mode=='empty' else
    (b'synthetic cloud error' if mode=='error' else (b'\x00'*(2*1024*1024) if mode=='large' else expected)))
  assert body==target,(name,mode,len(body))
  assert status==(503 if mode=='error' else 200),(name,mode,status)
  assert 'Content-Encoding' not in headers
  headers.pop('Date',None)
  results[name].append([status,headers,hashlib.sha256(body).hexdigest()])
assert results['baseline']==results['off']==results['on']==results['fault'],'recorder changed HTTP output'
seen=json.loads(get('http://cloud:8080/seen')[2])
# aiohttp may retry an idempotent PUT once after the synthetic connection drop.
non_drop=[r for r in seen if '/drop' not in r[1]]
assert len(non_drop)==len(hosts)*(len(modes)-1),len(non_drop)
assert all(r[0]=='PUT' and r[2]=='6f706171756500ff' and r[3]=='Basic c3ludGhldGljOnRlc3Q=' and r[4]=='identity' for r in seen)
deadline=time.monotonic()+10
while True:
 health=json.loads(get('http://'+hosts['fault']+':8642/api/health')[2])
 if health['diagnostics']['write_errors']>0:break
 assert time.monotonic()<deadline
 time.sleep(.05)
print(json.dumps({'runtime_machine':platform.machine(),'python':sys.version.split()[0],
 'http_exchanges':len(hosts)*len(modes),'forwarding_equivalent':True,'fault_write_errors':health['diagnostics']['write_errors'],
 'cloud_requests':len(seen),'drop_requests':sum('/drop' in r[1] for r in seen)}))
'''

VERIFY = r'''
import base64,gzip,hashlib,json,os,stat,sys,time
from pathlib import Path
sys.path.insert(0,'/app');import aiohttp,bridge_diagnostics
p=Path('/data/diagnostics')
for attempt in range(200):
 paths=sorted(p.glob('*.jsonl'))
 try:events=[json.loads(line) for f in paths for line in f.read_text().splitlines()]
 except (ValueError,OSError):time.sleep(.05);continue
 if any(e['event']=='capture_gap' for e in events) and len([e for e in events if e['event']=='response_write_complete'])==9:break
 time.sleep(.05)
else:raise AssertionError('capture did not drain')
assert all(stat.S_IMODE(f.stat().st_mode)==0o600 for f in paths)
assert stat.S_IMODE(p.stat().st_mode)==0o700
assert all(f.stat().st_size<=8*1024*1024 for f in paths)
pairs={}
for e in events:
 if 'correlation_id' in e:pairs.setdefault(e['correlation_id'],[]).append(e)
 if 'body' in e:
  b=e['body'];raw=base64.b64decode(b['base64'],validate=True)
  assert len(raw)==b['length'] and raw.decode('latin-1')==b['text_latin1']
assert len(pairs)==9
by_path={next(e['path'] for e in es if e['event']=='request_started'):es for es in pairs.values()}
for path,es in by_path.items():
 complete=next(e for e in es if e['event']=='response_write_complete')
 assert complete['device_execution']=='unconfirmed'
 if path.endswith(('/drop','/badgzip')):
  assert next(e for e in es if e['event']=='response_ready')['source']=='local'
 elif not path.endswith('/large'):
  assert next(e for e in es if e['event']=='response_ready')['source']=='cloud'
gz=by_path['/case/gzip'];raw=next(e for e in gz if e['event']=='cloud_response_body')
out=next(e for e in gz if e['event']=='response_ready')
assert raw['decompressed'] is False and out['decompressed'] is True
assert gzip.decompress(base64.b64decode(raw['body']['base64']))==base64.b64decode(out['body']['base64'])
assert any(e['event']=='capture_gap' for e in events)
assert not any('same' in json.dumps(e) or 'synthetic-cookie' in json.dumps(e) or 'Basic' in json.dumps(e) for e in events)
print(json.dumps({'capture_pairs':len(pairs),'binary_bodies_valid':True,'gzip_raw_and_decoded':True,
 'explicit_gaps':True,'private_posix_modes':True,'aiohttp':aiohttp.__version__,
 'app_hashes':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/app').glob('*.py')}}))
'''

ROTATION_PROBE = r'''
import asyncio,json,sys,time
from pathlib import Path
sys.path.insert(0,'/app')
from bridge_diagnostics import Capture
async def run():
    p=Path('/data/rotation-probe');p.mkdir(mode=0o700)
    old=p/'capture.1.jsonl';old.write_text('{"historical":true}\n');old.chmod(0o644)
    capture=Capture(p,max_bytes=16384,files=3)
    for _ in range(40):capture.emit(None,'synthetic_rotation',body=b'a'*900)
    capture.emit(None,'oversized',body=b'\x00'*3000)
    deadline=time.monotonic()+10
    while capture.pending_bytes:
        assert time.monotonic()<deadline
        await asyncio.sleep(.01)
    await capture.close()
    paths=list(p.glob('*.jsonl'))
    assert len(paths)==3 and all(f.stat().st_size<=16384 for f in paths)
    assert all(f.stat().st_mode&0o777==0o600 for f in paths)
    events=[json.loads(line) for f in paths for line in f.read_text().splitlines()]
    assert any(e['event']=='capture_gap' for e in events)
    assert any(e.get('rotation',{}).get('oldest_file_evicted') for e in events)
    assert any(e['event']=='session_end' for e in events)
asyncio.run(run())
print('arm64_rotation_gap_permissions=true')
'''

EXPORT = r'''
import hashlib,json,tarfile
from pathlib import Path
p=Path('/data')
assert (p/'prior-state.bin').read_bytes()==b'synthetic persistent state\x00\xff'
for name in ('diagnostics','rotation-probe'):
    events=[json.loads(line) for f in (p/name).glob('*.jsonl') for line in f.read_text().splitlines()]
    assert any(e['event']=='session_end' for e in events),name
    assert any(e['event']=='capture_gap' for e in events),name
hashes={'data/'+str(f.relative_to(p)).replace('\\','/'):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in p.rglob('*') if f.is_file()}
with tarfile.open('/synthetic-data.tar.gz','w:gz') as t:t.add(p,arcname='data')
print(json.dumps({'hashes':hashes}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--platform", default="linux/arm64")
    args = parser.parse_args()
    prefix = "bm-audit-" + uuid.uuid4().hex[:12]
    owned = []
    network = volume = None

    def docker(*command):
        result = subprocess.run(["docker", "--context", "desktop-linux", *command],
                                capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(f"docker {command[0]} failed: {result.stderr}")
        return (result.stdout + (result.stderr if command[0] == "logs" else "")).strip()

    try:
        image = json.loads(docker("image", "inspect", args.image))[0]
        assert image["Architecture"] == args.platform.split("/")[1]
        network = docker("network", "create", "--internal", "--label", "codex.braumeister.audit=" + prefix, prefix)
        assert json.loads(docker("network", "inspect", network))[0]["Internal"] is True
        volume = docker("volume", "create", "--label", "codex.braumeister.audit=" + prefix, prefix)
        with tempfile.TemporaryDirectory(prefix="bm-synthetic-") as folder:
            folder = Path(folder)

            def create(role, code, *extra):
                name = prefix + "-" + role
                identity = docker("create", "--platform", args.platform, "--name", name,
                                  "--network", network, "--network-alias", role,
                                  "--label", "codex.braumeister.audit=" + prefix,
                                  "--entrypoint", "python3", *extra, args.image, "/smoke.py")
                owned.append(identity)
                script = folder / (role + ".py")
                script.write_text(code, encoding="utf-8")
                docker("cp", str(script), identity + ":/smoke.py")
                return identity, name

            cloud, _ = create("cloud", CLOUD)
            docker("start", cloud)
            apps = {}
            hosts = {}
            for mode in ("baseline", "off", "on", "fault"):
                storage = ("--mount", "type=volume,src=" + volume + ",dst=/data") if mode == "on" else (
                    "--tmpfs", "/data:rw,noexec,nosuid,size=64m")
                identity, name = create(mode, BOOT, *storage,
                                        "--env", "SMOKE_MODE=" + mode)
                apps[mode], hosts[mode] = identity, name
                if mode == "baseline":
                    source = Path(__file__).resolve().parent / "fixtures/bridge_030.py"
                    docker("cp", str(source), identity + ":/app/bridge.py")
                docker("start", identity)
            driver, _ = create("driver", DRIVER.replace("json.loads(sys.argv[1])", repr(hosts)))
            docker("start", driver)
            try:
                code = docker("wait", driver)
            except Exception:
                for identity in owned:
                    print(docker("logs", identity)[-4000:], flush=True)
                raise
            logs = docker("logs", driver)
            if code != "0":
                for name, identity in apps.items():
                    print(name, docker("logs", identity)[-3000:], flush=True)
                raise RuntimeError("synthetic driver failed: " + logs)
            print(logs, flush=True)
            print(docker("exec", apps["on"], "python3", "-c", VERIFY), flush=True)
            assert docker("exec", apps["off"], "python3", "-c",
                          "from pathlib import Path; assert not Path('/data/diagnostics').exists(); print('disabled_no_files=true')")
            expected = {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                        for f in (Path(__file__).resolve().parents[1] / "braumeister_bridge/app").glob("*.py")}
            inside = json.loads(docker("exec", apps["on"], "python3", "-c",
                "import hashlib,json;from pathlib import Path;print(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in Path('/app').glob('*.py')}))"))
            assert expected == inside, "image does not contain the currently reviewed sources"
            print(docker("exec", apps["on"], "python3", "-c", ROTATION_PROBE), flush=True)
            # Capture must be closed before a consistent backup. Own volume only.
            docker("stop", "--time", "5", apps["on"])
            stopped = json.loads(docker("inspect", apps["on"]))[0]["State"]
            assert stopped["ExitCode"] == 0 and not stopped["OOMKilled"], stopped
            exporter = docker("create", "--platform", args.platform, "--network", "none",
                              "--label", "codex.braumeister.audit=" + prefix,
                              "--mount", "type=volume,src=" + volume + ",dst=/data,readonly",
                              "--entrypoint", "python3", args.image, "-c", EXPORT)
            owned.append(exporter)
            docker("start", exporter)
            assert docker("wait", exporter) == "0", docker("logs", exporter)
            export_info = json.loads(docker("logs", exporter))
            export_path = folder / "synthetic-data.tar.gz"
            docker("cp", exporter + ":/synthetic-data.tar.gz", str(export_path))
            with tarfile.open(export_path) as archive:
                actual = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                          for m in archive.getmembers() if m.isfile()}
            assert actual == export_info["hashes"], "export omitted or changed persistent files"
            print(json.dumps({"synthetic_data_export_complete": True,
                              "files": len(actual), "session_end_present": True}), flush=True)
            print(json.dumps({"image_id": image["Id"], "image_architecture": image["Architecture"],
                              "internal_network": True, "reviewed_source_hashes_match": True}), flush=True)
    finally:
        for identity in reversed(owned):
            docker("rm", "--force", identity)
        if network:
            docker("network", "rm", network)
        if volume:
            docker("volume", "rm", volume)
        print("owned_test_containers_network_and_volume_removed=true", flush=True)


if __name__ == "__main__":
    main()
