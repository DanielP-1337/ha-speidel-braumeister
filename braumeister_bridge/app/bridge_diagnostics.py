"""Optional, bounded, best-effort local traffic evidence. Never replays traffic."""
from __future__ import annotations

import asyncio
import base64
from collections import deque
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import threading
import time
import uuid

_LOGGER = logging.getLogger("braumeister_bridge")
SCHEMA_VERSION = 2  # protocol headers are ordered pairs, preserving duplicates
HEADER_ALLOWLIST = frozenset({
    "content-type", "content-length", "content-encoding", "transfer-encoding", "accept-encoding",
})


def protocol_headers(headers):
    """An allowlist, not a list of known secret header names."""
    return [(k.lower(), v) for k, v in headers.items() if k.lower() in HEADER_ALLOWLIST]


def stamp():
    return {
        "utc": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "monotonic_ns": time.monotonic_ns(),
    }


def _encode(value):
    if isinstance(value, bytes):
        return {
            "length": len(value), "base64": base64.b64encode(value).decode("ascii"),
            "text_latin1": value.decode("latin-1"),
        }
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_encode(v) for v in value]
    return value


def _weight(value):
    # Upper bound before base64/JSON allocation (Latin-1 controls need six JSON
    # bytes each, plus base64). Also conservatively accounts retained containers.
    if isinstance(value, bytes):
        return len(value) * 8 + 256
    if isinstance(value, str):
        return len(value) * 12 + 128  # non-BMP text is escaped as a surrogate pair
    if isinstance(value, dict):
        return 256 + sum(_weight(k) + _weight(v) for k, v in value.items())
    if isinstance(value, (tuple, list)):
        return 128 + sum(_weight(v) for v in value)
    return 64


class Capture:
    """One daemon writer; producers never wait for filesystem or queue space.

    Sequence numbers include rejected events. The next successful write (or a
    graceful close) marks all missing sequences. On disk failure the health
    counters/log remain available even when the gap itself cannot be persisted.
    """

    def __init__(self, directory: Path, max_bytes=8 * 1024 * 1024, files=4,
                 queue_items=64, queue_bytes=16 * 1024 * 1024):
        self.directory = directory
        self.max_bytes = max_bytes
        self.files = files
        self.queue_bytes = queue_bytes
        self.session = uuid.uuid4().hex
        self.sequence = 0
        self.pending_bytes = 0
        self.dropped = 0
        self.write_errors = 0
        self.last_written = 0
        self.queue = deque()
        self.queue_items = queue_items
        self.directory_checked = False
        self.storage_incompatible = False
        self.close_timed_out = False
        self.end_event_failed = False
        self.stopping = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, name="bridge-diagnostics", daemon=True)
        self.thread.start()
        self.emit(None, "session_start", max_file_bytes=max_bytes, retained_files=files,
                  retention="oldest files are overwritten; export before eviction",
                  previous_session_tail="unknown until previous session_end is found")

    def emit(self, context, event, **data):
        # Defense in depth: no diagnostic exception may escape into the bridge.
        try:
            self.sequence += 1
            item = {"schema": SCHEMA_VERSION, "session": self.session, "sequence": self.sequence,
                    "event": event, **stamp(), **data}
            if context:
                item["correlation_id"] = context[0]
                item["duration_ns"] = item["monotonic_ns"] - context[1]
            weight = _weight(item)
            if not self.lock.acquire(blocking=False):
                self.dropped += 1
                return
            try:
                if (self.stopping.is_set() or len(self.queue) >= self.queue_items
                        or weight > min(self.max_bytes - 512, self.queue_bytes - self.pending_bytes)):
                    self.dropped += 1
                    return
                self.pending_bytes += weight
                self.queue.append((item, weight))
            finally:
                self.lock.release()
        except Exception:
            self.dropped += 1

    def status(self):
        return {"session": self.session, "events_attempted": self.sequence,
                "events_written_through": self.last_written, "dropped_events": self.dropped,
                "write_errors": self.write_errors, "writer_alive": self.thread.is_alive(),
                "storage_incompatible": self.storage_incompatible,
                "close_timed_out": self.close_timed_out, "end_event_failed": self.end_event_failed}

    async def close(self):
        try:
            self.emit(None, "session_end")
        except Exception:
            self.end_event_failed = True
        finally:
            self.stopping.set()
        # Do not depend on default-executor availability to start the deadline.
        deadline = time.monotonic() + 1.0
        while self.thread.is_alive() and time.monotonic() < deadline:
            await asyncio.sleep(0.01)
        if self.thread.is_alive():
            self.close_timed_out = True

    def _path(self, index=0):
        return self.directory / ("capture.jsonl" if index == 0 else f"capture.{index}.jsonl")

    def _write(self, record):
        # Runs only on the writer thread. No headers, cookies or URLs in errors.
        if _weight(record) > self.max_bytes - 512:
            raise ValueError("diagnostic event exceeds conservative serialization budget")
        line = (json.dumps(_encode(record), ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
        if len(line) > self.max_bytes:
            raise ValueError("diagnostic event exceeds file limit")
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.directory.is_symlink():
            raise OSError("diagnostic directory must not be a symlink")
        self.directory.chmod(0o700)
        if not getattr(self, "directory_checked", False):
            # Do not silently exceed changed limits, or delete old evidence.
            # Fail closed until an operator privately exports/clears old files.
            with os.scandir(self.directory) as entries:
                for entry in entries:
                    match = re.fullmatch(r"capture(?:\.(\d+))?\.jsonl", entry.name)
                    if not match:
                        continue
                    # Windows scandir's cached stat may report st_nlink=0.
                    stat = os.stat(entry.path, follow_symlinks=False)
                    index = int(match[1] or 0)
                    if (entry.is_symlink() or not entry.is_file(follow_symlinks=False)
                            or stat.st_nlink != 1 or index >= self.files or self._path(index).name != entry.name
                            or stat.st_size > self.max_bytes):
                        self.storage_incompatible = True
                        raise OSError("existing capture storage is incompatible; export before reusing")
                    os.chmod(entry.path, 0o600)
            self.directory_checked = True
            self.storage_incompatible = False
        paths = [self._path(i) for i in range(self.files)]
        if any(p.is_symlink() or (p.exists() and p.stat().st_nlink != 1) for p in paths):
            raise OSError("diagnostic files must not be symlinks")
        path = paths[0]
        # A crash/power loss can leave a torn final line. Keep the evidence but
        # put the next record on a new line and explicitly mark the boundary.
        prefix = b""
        if path.exists() and path.stat().st_size:
            with path.open("rb") as previous:
                previous.seek(-1, os.SEEK_END)
                if previous.read(1) != b"\n":
                    prefix = b"\n"
                    record = {**record, "preceding_unterminated_record": True}
                    line = (json.dumps(_encode(record), ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
        if len(prefix) + len(line) > self.max_bytes:
            raise ValueError("diagnostic event exceeds file limit")
        if path.exists() and path.stat().st_size + len(prefix) + len(line) > self.max_bytes:
            record = {**record, "rotation": {"oldest_file_evicted": paths[-1].exists(),
                      "history_may_start_mid_exchange": True}}
            line = (json.dumps(_encode(record), ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
            for i in range(self.files - 1, 0, -1):
                if paths[i - 1].exists():
                    os.replace(paths[i - 1], paths[i])
            prefix = b""
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_BINARY", 0), 0o600)
        try:
            os.chmod(path, 0o600)
            before = os.fstat(fd).st_size
            try:
                remaining = memoryview(prefix + line)
                while remaining:
                    written = os.write(fd, remaining)
                    if written <= 0:
                        raise OSError("short diagnostic write")
                    remaining = remaining[written:]
            except Exception:
                os.ftruncate(fd, before)  # remove any partial JSON line if possible
                raise
        finally:
            os.close(fd)

    def _gap(self, first, last):
        return {"schema": SCHEMA_VERSION, "session": self.session, "event": "capture_gap", **stamp(),
                "first_missing_sequence": first, "last_missing_sequence": last,
                "reason": "queue_or_size_limit_or_write_failure", "write_errors": self.write_errors}

    def _run(self):
        warned = False
        while True:
            with self.lock:
                pending = self.queue.popleft() if self.queue else None
            if pending is None:
                if self.stopping.is_set():
                    break
                self.stopping.wait(0.02)  # only the background writer waits
                continue
            item, weight = pending
            try:
                seq = item["sequence"]
                if seq > self.last_written + 1:
                    self._write(self._gap(self.last_written + 1, seq - 1))
                    self.last_written = seq - 1
                self._write(item)
                self.last_written = seq
                warned = False
            except Exception:
                self.dropped += 1
                self.write_errors += 1
                if not warned:
                    _LOGGER.warning("Diagnostic capture lost events; inspect local health counters and capture_gap records")
                    warned = True
            finally:
                with self.lock:
                    self.pending_bytes -= weight
        if self.sequence > self.last_written:
            try:
                self._write(self._gap(self.last_written + 1, self.sequence))
            except Exception:
                _LOGGER.warning("Diagnostic final gap could not be saved; capture tail is incomplete")
