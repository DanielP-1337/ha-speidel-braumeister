"""Synthetic evidence only; local HTTP servers, no cloud/device traffic."""
import asyncio
import base64
from contextlib import asynccontextmanager
import errno
import gzip
import json
from pathlib import Path
import threading
from unittest.mock import AsyncMock
import zlib

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer, make_mocked_request
import pytest

from bridge_diagnostics import Capture
from conftest import FIXTURES
from test_bridge import DEVICE_HEADERS


def records(directory):
    paths = sorted(directory.glob("capture.*.jsonl"), key=lambda p: int(p.name.split(".")[1]), reverse=True)
    paths += list(directory.glob("capture.jsonl"))
    return [json.loads(line) for path in paths for line in path.read_text().splitlines()]


def body(event):
    value = event["body"]
    result = base64.b64decode(value["base64"], validate=True)
    assert len(result) == value["length"]
    assert value["text_latin1"].encode("latin-1") == result
    return result


async def drain(capture):
    deadline = asyncio.get_running_loop().time() + 10
    while capture.pending_bytes and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.01)
    assert not capture.pending_bytes, "test writer did not drain"


@asynccontextmanager
async def rig(module, directory, handler=None, enabled=True, passthrough=""):
    cloud = None
    if handler:
        app = web.Application()
        app.router.add_route("*", "/{tail:.*}", handler)
        cloud = TestServer(app)
        await cloud.start_server()
    options = {**module.DEFAULTS, "cloud_url": str(cloud.make_url("")) if cloud else "http://127.0.0.1:9",
               "state_file": "", "diagnostics_enabled": enabled, "diagnostics_directory": str(directory),
               "passthrough_url": passthrough}
    bridge = module.Bridge(options)
    await bridge.start_session()
    port80, api = module.build_apps(bridge)
    client, health = TestClient(TestServer(port80)), TestClient(TestServer(api))
    await client.start_server()
    await health.start_server()
    try:
        yield bridge, client, health
    finally:
        await client.close()
        await health.close()
        if bridge.capture:
            await drain(bridge.capture)
        await bridge.close_session()
        if cloud:
            await cloud.close()


@pytest.mark.parametrize("payload", [b"", b"unknown\r\nmessage\n\x00\xff", bytes(range(256)) * 20])
@pytest.mark.parametrize("encoding", ["", "gzip", "deflate", "raw-deflate"])
async def test_complete_binary_bodies_and_compression(bridge_module, tmp_path, payload, encoding):
    answer = b"Start\r\n$unknown=\xff\r\n$k=4\r\n" + payload + b"\r\nOK\r\nDone\r\n"
    wire = gzip.compress(answer) if encoding == "gzip" else answer
    if encoding in ("deflate", "raw-deflate"):
        compressor = zlib.compressobj(wbits=-15 if encoding == "raw-deflate" else 15)
        wire = compressor.compress(answer) + compressor.flush()
    seen = []

    async def cloud(request):
        seen.append(await request.read())
        assert request.headers["Accept-Encoding"] == "identity"
        return web.Response(status=202, body=wire, headers={
            "Content-Encoding": "deflate" if encoding == "raw-deflate" else encoding or "identity",
            "Set-Cookie": "private-cloud-cookie", "X-Private": "secret-header",
        })

    async with rig(bridge_module, tmp_path, cloud) as (bridge, client, health):
        response = await client.post("/braumeister/connect?token=private-query", data=payload,
                                     headers={**DEVICE_HEADERS, "Cookie": "private-browser-cookie"},
                                     auto_decompress=False)
        assert response.status == 202
        assert await response.read() == answer
        assert "Content-Encoding" not in response.headers
        assert seen == [payload]  # no additional queries or polling
        assert (await (await health.get("/api/health")).json())["diagnostics"]["writer_alive"]
    events = records(tmp_path)
    selected = [e for e in events if "correlation_id" in e]
    assert len({e["correlation_id"] for e in selected}) == 1
    assert [e["monotonic_ns"] for e in selected] == sorted(e["monotonic_ns"] for e in selected)
    assert all(e["utc"].endswith("+00:00") and "." in e["utc"] for e in selected)
    request_event = next(e for e in selected if e["event"] == "request_body")
    raw = next(e for e in selected if e["event"] == "cloud_response_body")
    outgoing = next(e for e in selected if e["event"] == "response_ready")
    assert body(request_event) == payload
    assert body(raw) == wire and raw["decompressed"] is False
    assert body(outgoing) == answer and outgoing["decompressed"] is bool(encoding)
    assert outgoing["source"] == "cloud"
    assert selected[-1]["event"] == "response_write_complete"
    assert selected[-1]["device_execution"] == "unconfirmed"
    text = json.dumps(events)
    for secret in ("private-query", "private-cloud-cookie", "private-browser-cookie", "secret-header", "Basic"):
        assert secret not in text
    assert next(e for e in selected if e["event"] == "request_started")["query_omitted"]


async def test_disabled_has_no_writer_files_or_api_change(bridge_module, tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("disabled diagnostics must not construct a writer")
    monkeypatch.setattr(bridge_module, "Capture", forbidden)
    async with rig(bridge_module, tmp_path, enabled=False) as (bridge, client, health):
        response = await client.post("/braumeister/connect", data=b"unknown", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER
        assert bridge.capture is None
        assert await (await health.get("/api/health")).json() == {"ok": True, "devices": 0}
    assert not list(tmp_path.iterdir())


async def test_disabled_preserves_existing_capture_and_unrelated_data(bridge_module, tmp_path):
    previous = tmp_path / "capture.jsonl"
    previous.write_bytes(b'{"synthetic_previous_session":true}\n')
    unrelated = tmp_path / "prior-state.bin"
    unrelated.write_bytes(b"synthetic persistent data\x00\xff")
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    async with rig(bridge_module, tmp_path, enabled=False) as (_, client, _):
        response = await client.post("/braumeister/connect", data=b"opaque", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER
    after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    assert after == before


async def test_foreign_passthrough_not_recorded(bridge_module, tmp_path):
    async def foreign(request):
        return web.Response(body=await request.read())
    app = web.Application()
    app.router.add_post("/foreign", foreign)
    async with TestServer(app) as target:
        async with rig(bridge_module, tmp_path, passthrough=str(target.make_url(""))) as (_, client, _):
            response = await client.post("/foreign", data=b"foreign private payload", headers={"Host": "other.invalid"})
            assert await response.read() == b"foreign private payload"
    assert [e["event"] for e in records(tmp_path)] == ["session_start", "session_end"]


@pytest.mark.parametrize("fault", ["connection", "gzip", "unsupported", "http_error", "disabled_forward"])
async def test_errors_and_local_fallback_are_distinct(bridge_module, tmp_path, fault):
    async def cloud(request):
        if fault == "http_error":
            return web.Response(status=503, body=b"cloud unavailable")
        return web.Response(body=b"bad encoding", headers={"Content-Encoding": "gzip" if fault == "gzip" else "br"})
    async with rig(bridge_module, tmp_path, None if fault == "connection" else cloud) as (bridge, client, _):
        if fault == "disabled_forward":
            bridge.options["forward_to_cloud"] = False
        response = await client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS)
        result = await response.read()
        assert response.status == (503 if fault == "http_error" else 200)
        assert result == (b"cloud unavailable" if fault == "http_error" else bridge_module.LOCAL_ANSWER)
    events = records(tmp_path)
    ready = next(e for e in events if e["event"] == "response_ready")
    assert ready["source"] == ("cloud" if fault == "http_error" else "local")
    assert any(e["event"] == "cloud_error" for e in events) == (fault in ("connection", "gzip", "unsupported"))
    if fault in ("gzip", "unsupported"):
        assert body(next(e for e in events if e["event"] == "cloud_response_body")) == b"bad encoding"


async def test_truncated_cloud_transfer_is_not_a_complete_body(bridge_module, tmp_path):
    async def cloud(request):
        response = web.StreamResponse(headers={"Content-Length": "100"})
        await response.prepare(request)
        await response.write(b"partial")
        request.transport.close()
        return response
    async with rig(bridge_module, tmp_path, cloud) as (_, client, _):
        response = await client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER
    events = records(tmp_path)
    error = next(e for e in events if e["event"] == "cloud_response_read_error")
    assert error["complete"] is False and error["body_available"] is False
    assert not any(e["event"] == "cloud_response_body" for e in events)


@pytest.mark.parametrize("stage", ["read", "write"])
async def test_device_read_and_write_aborts(bridge_module, tmp_path, monkeypatch, stage):
    bridge = bridge_module.Bridge({**bridge_module.DEFAULTS, "state_file": "", "forward_to_cloud": False})
    bridge.capture = Capture(tmp_path)
    request = make_mocked_request("POST", "/braumeister/connect", headers=DEVICE_HEADERS)
    monkeypatch.setattr(type(request), "read", AsyncMock(side_effect=ConnectionResetError() if stage == "read" else None,
                                                        return_value=b""))
    if stage == "write":
        monkeypatch.setattr(web.StreamResponse, "prepare", AsyncMock(side_effect=ConnectionResetError()))
    with pytest.raises(ConnectionResetError):
        await bridge.handle_device(request)
    await bridge.capture.close()
    events = records(tmp_path)
    assert events[-2]["event"] == ("request_read_error" if stage == "read" else "response_write_error")
    assert not any(e["event"] == "response_write_complete" for e in events)


async def test_rotation_and_oversized_event_mark_gaps(tmp_path):
    capture = Capture(tmp_path, max_bytes=16384, files=3)
    for _ in range(40):
        capture.emit(None, "synthetic", body=b"a" * 900)
    capture.emit(None, "too_large", body=b"\x00" * 3000)
    capture.emit(None, "after_gap")
    await drain(capture)
    await capture.close()
    paths = list(tmp_path.iterdir())
    assert len(paths) == 3
    assert all(p.stat().st_size <= 16384 for p in paths)
    events = records(tmp_path)
    assert events[0].get("sequence", 0) > 1  # bounded retention evicted the beginning
    assert any(e["event"] == "capture_gap" and e["first_missing_sequence"] == 42 for e in events)
    assert capture.status()["dropped_events"] == 1
    assert events[-1]["event"] == "session_end"
    for e in events:
        if e["event"] == "synthetic":
            assert body(e) == b"a" * 900


async def test_full_disk_does_not_break_forwarding_and_recovers(bridge_module, tmp_path, monkeypatch):
    original = Capture._write
    fail = threading.Event()
    fail.set()
    failed = threading.Event()
    def write(self, record):
        if fail.is_set():
            failed.set()
            raise OSError(errno.ENOSPC, "disk full")
        return original(self, record)
    monkeypatch.setattr(Capture, "_write", write)
    async with rig(bridge_module, tmp_path) as (bridge, client, health):
        assert await asyncio.to_thread(failed.wait, 2)
        response = await client.post("/braumeister/connect", data=b"unknown", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER
        assert (await (await health.get("/api/health")).json())["diagnostics"]["write_errors"] > 0
        fail.clear()
    assert any(e["event"] == "capture_gap" for e in records(tmp_path))


async def test_blocked_writer_and_queue_overflow_do_not_block_forwarding(bridge_module, tmp_path, monkeypatch):
    original = Capture._write
    entered, release = threading.Event(), threading.Event()
    def slow(self, record):
        entered.set()
        assert release.wait(5)
        return original(self, record)
    monkeypatch.setattr(Capture, "_write", slow)
    capture = Capture(tmp_path, queue_items=1)
    assert await asyncio.to_thread(entered.wait, 2)
    capture.emit(None, "fill")
    capture.emit(None, "dropped")
    async def cloud(request):
        return web.Response(body=b"unchanged cloud reply")
    async with rig(bridge_module, tmp_path / "other", cloud, enabled=False) as (bridge, client, _):
        bridge.capture = capture
        try:
            response = await asyncio.wait_for(client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS), 2)
            assert await response.read() == b"unchanged cloud reply"
            assert capture.status()["dropped_events"] > 0
        finally:
            release.set()
    assert any(e["event"] == "capture_gap" for e in records(tmp_path))


async def test_byte_budget_rejects_without_silent_truncation(tmp_path):
    capture = Capture(tmp_path, queue_bytes=4096)
    capture.emit(None, "too_large_for_queue", body=b"a" * 2000)
    await capture.close()
    assert capture.status()["dropped_events"] >= 1
    assert any(e["event"] == "capture_gap" for e in records(tmp_path))
    assert not any(e["event"] == "too_large_for_queue" for e in records(tmp_path))


async def test_capture_fault_is_contained(bridge_module, tmp_path, monkeypatch):
    async with rig(bridge_module, tmp_path) as (bridge, client, _):
        def broken(*args, **kwargs):
            raise RuntimeError("unexpected diagnostic fault")
        monkeypatch.setattr(bridge.capture, "emit", broken)
        response = await client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER


def test_partial_disk_write_rolls_back_line(tmp_path, monkeypatch):
    capture = Capture.__new__(Capture)
    capture.directory, capture.max_bytes, capture.files = Path(tmp_path), 16384, 3
    capture._write({"event": "before"})
    original = (tmp_path / "capture.jsonl").read_bytes()
    import os
    write = os.write
    calls = []
    def short(fd, data):
        calls.append(True)
        if len(calls) > 1:
            raise OSError(errno.ENOSPC, "full")
        return write(fd, data[:5])
    monkeypatch.setattr(os, "write", short)
    with pytest.raises(OSError):
        capture._write({"event": "interrupted"})
    assert (tmp_path / "capture.jsonl").read_bytes() == original


async def test_restart_marks_torn_tail_and_new_session(tmp_path):
    (tmp_path / "capture.jsonl").write_bytes(b'{"torn":')
    capture = Capture(tmp_path)
    await capture.close()
    lines = (tmp_path / "capture.jsonl").read_text().splitlines()
    assert lines[0] == '{"torn":'
    start = json.loads(lines[1])
    assert start["event"] == "session_start" and start["preceding_unterminated_record"]
    assert start["sequence"] == 1


async def test_writer_init_failure_keeps_bridge_running(bridge_module, tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("thread unavailable")
    monkeypatch.setattr(bridge_module, "Capture", unavailable)
    async with rig(bridge_module, tmp_path) as (bridge, client, health):
        response = await client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS)
        assert await response.read() == bridge_module.LOCAL_ANSWER
        assert bridge.capture is None
        assert (await (await health.get("/api/health")).json())["diagnostics"]["startup_failed"]


@pytest.mark.parametrize("case", json.loads((FIXTURES / "diagnostic_transport.json").read_text())["cases"],
                         ids=lambda case: case["name"])
async def test_synthetic_fixture_and_disabled_equivalence(bridge_module, tmp_path, case):
    request_body = case["request_latin1"].encode("latin-1")
    response_body = case["response_latin1"].encode("latin-1")
    seen = []
    async def cloud(request):
        seen.append(await request.read())
        return web.Response(status=case["cloud_status"], body=response_body)
    received = []
    for enabled in (False, True):
        directory = tmp_path / str(enabled)
        async with rig(bridge_module, directory, cloud, enabled=enabled) as (_, client, _):
            response = await client.post("/braumeister/connect", data=request_body, headers=DEVICE_HEADERS,
                                         auto_decompress=False)
            received.append((response.status, dict(response.headers), await response.read()))
    assert seen == [request_body, request_body]
    # Date is generated by the HTTP stack and may cross a second boundary.
    for _, headers, _ in received:
        headers.pop("Date", None)
    assert received[0] == received[1]
    assert received[1][0] == case["cloud_status"] and received[1][2] == response_body
    events = records(tmp_path / "True")
    assert body(next(e for e in events if e["event"] == "request_body")) == request_body
    assert body(next(e for e in events if e["event"] == "response_ready")) == response_body


async def test_concurrent_requests_have_independent_pairs(bridge_module, tmp_path):
    async def cloud(request):
        return web.Response(body=b"reply:" + await request.read())
    async with rig(bridge_module, tmp_path, cloud) as (_, client, _):
        async def exchange(payload):
            response = await client.post("/braumeister/connect", data=payload, headers=DEVICE_HEADERS)
            assert await response.read() == b"reply:" + payload
        await asyncio.gather(*(exchange(f"unknown={i}".encode()) for i in range(3)))
    events = records(tmp_path)
    pairs = {}
    for event in events:
        if "correlation_id" in event:
            pairs.setdefault(event["correlation_id"], []).append(event)
    assert len(pairs) == 3
    for pair in pairs.values():
        incoming = body(next(e for e in pair if e["event"] == "request_body"))
        outgoing = body(next(e for e in pair if e["event"] == "response_ready"))
        assert outgoing == b"reply:" + incoming
        assert pair[-1]["event"] == "response_write_complete"
