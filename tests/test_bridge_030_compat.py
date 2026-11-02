"""Differential tests against the exact public source recovered from upstream 0.3.0."""
import ast
import gzip
import hashlib
import importlib.util
from pathlib import Path
import zlib

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
import pytest

BASE = Path(__file__).parent / 'fixtures/bridge_030.py'
spec = importlib.util.spec_from_file_location('baseline_030', BASE)
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def test_exact_legacy_baseline_and_unrelated_functions(bridge_module):
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == '50f7d628a155fca16345ae4036d039a8f481f7fa8e03d150ec7a0bc1284ccd27'
    before = ast.parse(BASE.read_text())
    after = ast.parse(Path(bridge_module.__file__).read_text())
    for name in ('PublicCloudResolver', 'DnsProtocol', 'record', 'log_state_change', 'device_for', 'passthrough', 'api_status'):
        def find(tree):
            return next(n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)
        assert ast.dump(find(before)) == ast.dump(find(after)), name
    assert {k: bridge_module.DEFAULTS[k] for k in legacy.DEFAULTS} == legacy.DEFAULTS
    assert bridge_module.DEFAULTS['diagnostics_enabled'] is False


@pytest.mark.parametrize('encoding', ['', 'identity', 'gzip', 'x-gzip', 'deflate', 'raw', 'gzip, deflate', 'badgzip', 'br'])
@pytest.mark.parametrize('status', [200, 207, 503])
async def test_legacy_http_equivalence(bridge_module, tmp_path, encoding, status):
    plain = bytes(range(256)) + b'\r\nsynthetic\x00\xff'
    wire = plain
    if encoding in ('gzip', 'x-gzip', 'gzip, deflate'):
        wire = gzip.compress(wire)
    if encoding in ('deflate', 'gzip, deflate'):
        wire = zlib.compress(wire)
    if encoding == 'raw':
        wire = zlib.compress(wire)[2:-4]
    if encoding == 'badgzip':
        wire = b'broken'
    seen = []
    async def cloud(request):
        seen.append((request.method, request.raw_path, await request.read(), request.headers.getall('Accept-Encoding')))
        headers = {'Date': 'Mon, 02 Nov 2026 00:00:00 GMT', 'X-Legacy': 'keep', 'ETag': 'synthetic', 'Digest': 'synthetic'}
        if encoding:
            headers['Content-Encoding'] = {'raw':'deflate', 'badgzip':'gzip'}.get(encoding, encoding)
        return web.Response(status=status, body=wire, headers=headers)
    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', cloud)
    server = TestServer(app)
    await server.start_server()
    results = []
    try:
        for module, enabled in ((legacy, False), (bridge_module, False), (bridge_module, True)):
            bridge = module.Bridge({**module.DEFAULTS, 'cloud_url': str(server.make_url('')),
                                    'diagnostics_enabled': enabled, 'diagnostics_directory': str(tmp_path)})
            await bridge.start_session()
            port, _ = module.build_apps(bridge)
            client = TestClient(TestServer(port), auto_decompress=False)
            await client.start_server()
            try:
                resp = await client.post('/synthetic?q=byte%2Ftest', data=plain,
                                         headers={'Host':'api2.myspeidel.com', 'accept-encoding':'gzip'})
                body = await resp.read()
                headers = dict(resp.headers)
                headers.pop('Date', None)
                results.append((resp.status, headers, body))
            finally:
                await client.close()
                await bridge.close_session()
        assert results[0] == results[1] == results[2]
        assert len(seen) == 3 and seen[0] == seen[1] == seen[2]
    finally:
        await server.close()
