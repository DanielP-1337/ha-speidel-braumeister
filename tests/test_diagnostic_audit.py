"""Fault-injection regressions from the independent 2026-11-02 audit."""
import asyncio
import builtins
import json
import os
import runpy
import threading
import time
from unittest.mock import AsyncMock

from aiohttp import web
from multidict import CIMultiDict
import pytest

import bridge_diagnostics as diagnostics
from bridge_diagnostics import Capture
from conftest import ROOT
from test_bridge import DEVICE_HEADERS
from test_bridge_diagnostics import drain, records, rig


@pytest.mark.parametrize("operation", ["headers", "context", "status", "emit"])
async def test_diagnostic_fault_does_not_change_cloud_reply(bridge_module, tmp_path, monkeypatch, operation):
    seen = []
    async def cloud(request):
        seen.append((request.method, request.raw_path, await request.read(), request.headers.get("Authorization")))
        return web.Response(status=207, body=b"unchanged cloud bytes")
    async with rig(bridge_module, tmp_path, cloud) as (bridge, client, health):
        def broken(*args, **kwargs):
            raise RuntimeError("synthetic diagnostic fault")
        if operation == "headers":
            monkeypatch.setattr(bridge_module, "protocol_headers", broken)
        elif operation == "context":
            monkeypatch.setattr(bridge_module.uuid, "uuid4", broken)
        elif operation == "status":
            monkeypatch.setattr(bridge.capture, "status", broken)
        else:
            monkeypatch.setattr(bridge.capture, "emit", broken)
        response = await client.put("/braumeister/connect?q=keep%2Fencoded", data=b"opaque\x00\xff",
                                    headers=DEVICE_HEADERS)
        assert response.status == 207
        assert await response.read() == b"unchanged cloud bytes"
        # Existing aiohttp URL canonicalization converts this escaped slash.
        assert seen == [("PUT", "/braumeister/connect?q=keep/encoded", b"opaque\x00\xff", DEVICE_HEADERS["Authorization"])]
        status = await health.get("/api/health")
        assert status.status == 200
        result = await status.json()
        if operation == "status":
            assert result["diagnostics"]["status_failed"]
        else:
            assert result["diagnostics"]["event_errors"] > 0


def test_producer_never_waits_for_writer_lock(tmp_path):
    capture = Capture(tmp_path)
    acquired, release = threading.Event(), threading.Event()
    def holder():
        with capture.lock:
            acquired.set()
            release.wait(0.5)
    holder_thread = threading.Thread(target=holder)
    holder_thread.start()
    assert acquired.wait(2)
    started = time.monotonic()
    try:
        capture.emit(None, "while_lock_held")
        elapsed = time.monotonic() - started
    finally:
        release.set()
        holder_thread.join(2)
        capture.stopping.set()
        capture.thread.join(2)
    assert elapsed < 0.2, "producer waited for a writer lock"
    assert capture.dropped > 0


def test_oversize_rejected_before_base64_or_json_allocation(tmp_path, monkeypatch):
    capture = Capture.__new__(Capture)
    capture.directory, capture.max_bytes, capture.files = tmp_path, 16384, 3
    def forbidden(value):
        raise AssertionError("encoding was entered before the size guard")
    monkeypatch.setattr(diagnostics, "_encode", forbidden)
    with pytest.raises(ValueError):
        capture._write({"body": b"\x00" * 20000})
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("old_file,old_size", [("capture.4.jsonl", 100), ("capture.jsonl", 20000)])
async def test_incompatible_old_limits_fail_closed_without_deleting_evidence(tmp_path, old_file, old_size):
    path = tmp_path / old_file
    original = b"x" * old_size
    path.write_bytes(original)
    capture = Capture(tmp_path, max_bytes=16384, files=3)
    capture.emit(None, "should_not_grow_storage")
    await capture.close()
    assert path.read_bytes() == original
    assert sum(p.stat().st_size for p in tmp_path.iterdir()) == old_size
    assert capture.status()["write_errors"] > 0
    assert capture.status()["storage_incompatible"]


def test_header_allowlist_preserves_duplicate_protocol_headers():
    headers = CIMultiDict([("Content-Encoding", "gzip"), ("Content-Encoding", "identity"),
                           ("X-New-Secret", "private"), ("Authorization", "private"), ("Cookie", "private")])
    assert diagnostics.protocol_headers(headers) == [("content-encoding", "gzip"), ("content-encoding", "identity")]


async def test_shutdown_is_bounded_when_recorder_close_hangs(bridge_module):
    bridge = bridge_module.Bridge({**bridge_module.DEFAULTS, "state_file": ""})
    class HungCapture:
        async def close(self):
            await asyncio.Event().wait()
    bridge.capture = HungCapture()
    await asyncio.wait_for(bridge.close_session(), timeout=2)
    assert bridge.capture_shutdown_failed


async def test_close_does_not_use_shared_default_executor(tmp_path, monkeypatch):
    capture = Capture(tmp_path)
    def forbidden(*args, **kwargs):
        raise AssertionError("shutdown used default executor")
    monkeypatch.setattr(asyncio, "to_thread", forbidden)
    await capture.close()
    assert not capture.thread.is_alive()


def test_missing_optional_module_does_not_break_normal_import(monkeypatch):
    original = builtins.__import__
    def unavailable(name, *args, **kwargs):
        if name == "bridge_diagnostics":
            raise ImportError("synthetic missing optional module")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", unavailable)
    module = runpy.run_path(str(ROOT / "braumeister_bridge/app/bridge.py"))
    assert module["Capture"] is None
    assert module["DEFAULTS"]["diagnostics_enabled"] is False


async def test_disabled_does_not_prepare_event_data(bridge_module, tmp_path, monkeypatch):
    async with rig(bridge_module, tmp_path, enabled=False) as (bridge, _, _):
        def forbidden():
            raise AssertionError("disabled diagnostics prepared data")
        bridge.capture_event(None, "synthetic", forbidden)
        assert bridge.capture_failures == 0


async def test_decompression_annotation_fault_keeps_cloud_bytes(bridge_module, tmp_path, monkeypatch):
    async def cloud(request):
        return web.Response(body=b"actual cloud reply")
    async with rig(bridge_module, tmp_path, cloud) as (bridge, client, _):
        original = bridge_module.web.Request.__setitem__
        def fault(request, key, value):
            if key == bridge_module._DECOMPRESSED_KEY:
                raise RuntimeError("annotation failed")
            return original(request, key, value)
        monkeypatch.setattr(bridge_module.web.Request, "__setitem__", fault)
        response = await client.post("/braumeister/connect", data=b"", headers=DEVICE_HEADERS)
        assert await response.read() == b"actual cloud reply"
        assert bridge.capture_failures > 0


async def test_cloud_cancellation_and_body_read_cancellation_are_visible(bridge_module, tmp_path, monkeypatch):
    bridge = bridge_module.Bridge({**bridge_module.DEFAULTS, "state_file": "", "cloud_url": "http://127.0.0.1:9"})
    bridge.capture = Capture(tmp_path)
    request = bridge_module.web.Request
    from aiohttp.test_utils import make_mocked_request
    fake = make_mocked_request("POST", "/braumeister/connect", headers=DEVICE_HEADERS)
    monkeypatch.setattr(request, "read", AsyncMock(return_value=b""))
    monkeypatch.setattr(bridge, "forward_to_cloud", AsyncMock(side_effect=asyncio.CancelledError()))
    with pytest.raises(asyncio.CancelledError):
        await bridge.handle_device(fake)
    await bridge.capture.close()
    assert any(e["event"] == "cloud_cancelled" for e in records(tmp_path))
    assert not any(e["event"] == "response_ready" for e in records(tmp_path))


async def test_rotation_marks_eviction_and_serialization_bound(tmp_path):
    capture = Capture(tmp_path, max_bytes=16384, files=2)
    for _ in range(40):
        capture.emit(None, "synthetic", body=b"a" * 900)
    await drain(capture)
    await capture.close()
    events = records(tmp_path)
    assert any(e.get("rotation", {}).get("oldest_file_evicted") for e in events)
    assert all(p.stat().st_size <= 16384 for p in tmp_path.iterdir())
    event = {"body": b"\x00\xff" * 1000, "astral": "\U0001f600" * 1000}
    size = len(json.dumps(diagnostics._encode(event), ensure_ascii=True).encode())
    assert diagnostics._weight(event) >= size


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission assertion; NTFS ACLs are different")
async def test_existing_archives_are_private(tmp_path):
    archive = tmp_path / "capture.1.jsonl"
    archive.write_text('{"historical":true}\n')
    archive.chmod(0o644)
    capture = Capture(tmp_path)
    await capture.close()
    assert archive.stat().st_mode & 0o777 == 0o600
    assert tmp_path.stat().st_mode & 0o777 == 0o700
