# Braumeister Bridge

Local preparation **0.3.1-diag.1**, based on the hardware-verified regular Bridge
0.3.0. Recorder installation/activation have not been authorized. See the
[current preparation plan](../docs/RECORDER_030_PREPARATION.md).

Receives the data your Speidel Braumeister sends to the My Speidel cloud, directly in Home
Assistant. The Speidel Braumeister integration then reads the status locally, about once per
second instead of via the web interface. The data is still forwarded to My Speidel, so the
app and the web interface keep working.

Works with Braumeisters with the WiFi module and firmware 1.1.27.

## How it works

The Braumeister looks up `api2.myspeidel.com` via DNS when it connects. This app

1. runs a small DNS server that answers this one name with the Home Assistant IP and forwards
   all other names to your normal DNS server,
2. receives the Braumeister's messages on port 80 and forwards them to My Speidel,
3. passes every other request on port 80 to another service if you configure one (see below),
4. provides the latest messages to the integration on `127.0.0.1:8642`.

## Setup

1. Install and start this app.
2. On the Braumeister, open the WiFi settings and set the **DNS server** to the IP address of
   your Home Assistant. Only the Braumeister uses this DNS server; the rest of your network is
   not affected.
3. Switch the Braumeister off and on again. It only looks up the server address when it
   connects.
4. The app log shows `DNS api2.myspeidel.com from <Braumeister IP>` and the integration starts
   using the local data (debug log: `Got data via Braumeister Bridge`).

## Port 80 is already in use

The Braumeister always connects to port 80. If another service on your Home Assistant host
already uses port 80, move it to another port and enter it as `passthrough_url`. The app then
forwards every request that is not from the Braumeister to it.

Example for `emulated_hue` (Alexa expects it on port 80):

```yaml
emulated_hue:
  listen_port: 8300
  advertise_port: 80
```

App option: `passthrough_url: http://127.0.0.1:8300`

## Options

| Option | Default | Meaning |
|---|---|---|
| `bridge_ip` | auto | IP returned for `api2.myspeidel.com`. Auto-detected from the host. |
| `cloud_host` | `api2.myspeidel.com` | Hostname the Braumeister talks to. |
| `forward_to_cloud` | `true` | Forward messages to My Speidel. If `false`, or if the cloud is unreachable, the app answers itself and My Speidel shows the device as offline. |
| `upstream_dns` | auto | DNS server for all other names. Auto-detected from the host. |
| `cloud_dns` | `[]` | Host resolver by default; explicitly set DNS servers without the local rewrite when needed. |
| `dns_port` | `53` | Port of the DNS server. `0` turns it off (if you use your own DNS). |
| `http_port` | `80` | Port for the Braumeister's messages. Must be 80 for a real device. |
| `passthrough_url` | empty | Where other requests on port 80 go, e.g. `http://127.0.0.1:8300`. |
| `api_port` | `8642` | Local status API for the integration (only reachable from the host). |
| `log_level` | `info` | `debug` logs every message. |


## Cloud DNS and AdGuard rewrites

The built-in DNS remains enabled on `dns_port: 53` by default. For an existing
AdGuard (or other DNS) rewrite of `api2.myspeidel.com` to the HA host, set
`dns_port: 0` to disable only the bridge's DNS listener. The device must actually
use that DNS server; some routers use a separate resolver on guest Wi-Fi.

By default, `cloud_dns: []` uses the host resolver. In the documented setup,
only the Braumeister uses the bridge's DNS, so no separate cloud resolver is
needed and no third-party DNS service is selected by the bridge.

For a network-wide AdGuard rewrite with `dns_port: 0`, configure `cloud_dns`
with a reachable DNS resolver that does not apply the local rewrite. For example,
`cloud_dns: ["1.1.1.1", "1.0.0.1"]` explicitly opts into Cloudflare; choose a
resolver permitted by your network and your DNS/privacy preferences instead if
appropriate. Outbound DNS to the configured resolver must be allowed.

Both resolver modes reject non-public answers to prevent forwarding loops. The
error message points to `cloud_dns`; failure retains the existing local response
behavior. `upstream_dns` still serves the built-in DNS forwarder for other names.
HTTP passthrough still uses the host resolver, so local targets continue to work.
Cloud redirects are not followed.

Cloud requests ask for identity encoding; gzip and both zlib-wrapped and raw
HTTP deflate responses are decoded if the server compresses anyway. Recipe
persistence and the device command-response format are unchanged.

## Optional local diagnostic capture

Disabled by default. This is a local preparation for observational protocol
analysis, not a control interface. It never sends a new command or cloud poll,
replays a captured request, or captures other-host HTTP passthrough traffic.
The regular Bridge 0.3.0 and Integration 2.0.11-beta now have owner-confirmed live
telemetry, cloud replies and matching displays. These are separate versions.
The new recorder build has not been installed or verified on HA.

```yaml
diagnostics_enabled: false
diagnostics_max_file_mb: 8
diagnostics_files: 4
```

Only after explicit deployment agreement, enable for a short experiment by
setting `diagnostics_enabled: true`. Limits apply to serialized bytes, not just
body length. The fixed directory is `/data/diagnostics` inside the app container;
the directory override used by tests is not an app option. There is no download
route. On POSIX the directory/files are restricted to owner permissions 0700/0600.
Windows tests do not establish NTFS ACL protection.

### Data and interpretation

JSONL events share a process-session ID and monotonically increasing sequence
number. The audited format is `schema: 2`: header fields contain ordered pairs,
preserving duplicates. Older schema-1 files used header dictionaries; readers
must honor each record's schema, including mixed retained sessions. Each device
HTTP exchange has a separate random `correlation_id`, UTC
timestamp with microseconds, monotonic nanoseconds and elapsed `duration_ns`.
Monotonic values compare only within the running process; UTC can jump if the
host clock is corrected. Microsecond formatting is not a guarantee of clock
accuracy. No device-provided time is substituted for capture time.

| Event | Evidence |
|---|---|
| `request_started` | Method, path (query deliberately omitted and flagged), allowlisted request headers |
| `request_body` | Complete application body read by aiohttp, including empty/unknown messages |
| `cloud_request_started` | Forwarding attempt; effective allowlisted headers (identity encoding requested) |
| `cloud_response_started` | Cloud HTTP status/allowlisted headers received; body-read timing starts here |
| `cloud_response_body` | Complete raw HTTP entity before content decompression; HTTP transfer chunk framing already removed |
| `cloud_error` / `cloud_cancelled` | Forwarding, read or decoding failed/cancelled; exception class only |
| `response_ready` | Actual intended device response body, status, source `cloud`/`local`, and decompression flag |
| `response_write_complete` | HTTP output completed; **device execution remains unconfirmed** |
| `request_read_error` / `cloud_response_read_error` | Incomplete read; partial bytes unavailable from the unchanged `read()` calls, explicitly flagged |
| `response_write_error` | HTTP output failed/cancelled; delivered byte count unknown |
| `session_start` / `session_end` | Session boundaries; absence of end means the tail is not known complete |
| `capture_gap` | One or more event sequences were not saved (queue/record-size/write failure) |
| `cloud_decoded` | Decoding decision recorded inside the diagnostic fault boundary |
| `diagnostic_event_error` | Event preparation/annotation failed; `failed_event` identifies the missing evidence |

Each body is `{length, base64, text_latin1}`. Base64 is authoritative; the
Latin-1 view is byte-preserving and JSON escapes controls. It is not an assertion
that the device uses Latin-1 as its semantic character encoding. No splitting,
parsing, command normalization or 200-byte truncation is applied to these bodies.
Request bodies are the aiohttp server application representation (content
decompression, when requested by a supported incoming Content-Encoding, occurs
inside aiohttp); the request flag identifies that case. The raw cloud body has
`decompressed: false`; the device response flags successful gzip/deflate decoding.
Invalid/unsupported compression retains the received raw cloud bytes and records
the existing local fallback. An HTTP 4xx/5xx received from the cloud remains a
cloud response; it is not confused with a connection failure/local 200 fallback.

Only Content-Type, Content-Length, Content-Encoding, Transfer-Encoding and
Accept-Encoding are saved as headers. These identify framing/representation and
the encoding preference. Cookies, Authorization, other headers and query values
are excluded, including unknown custom credential headers. Header pairs preserve
duplicate protocol headers; the forwarding implementation remains unchanged.
Paths are recorded as application paths and can themselves contain sensitive
segments; they are not automatically redacted. **Bodies still contain
device identifiers, signatures and possibly private recipes or application
secrets**: these are private raw evidence, not Git fixtures. Ordinary bridge logs
also retain their existing identifier/command logging behavior.

### Bounds, rotation and failure behavior

The writer runs in a daemon thread. Producers use a deque behind a **nonblocking**
lock acquisition; contention drops the event rather than waiting. The writer
releases that lock before any filesystem operation. Queue limits are 64 events
and a conservative 16 MiB retained-data/serialization estimate, including the
in-flight event. Body size checks use `len`, not a scan or an encoded copy in the
event loop. Full event preparation, context creation and annotation execute
inside a fault boundary; a disabled recorder does not evaluate the callbacks.
Status failures return diagnostic failure metadata while preserving normal API
health. Diagnostic errors do not invoke potentially blocking log handlers on the
HTTP path. Existing upstream recipe persistence and ordinary logging are not
changed and can still perform synchronous I/O; this guarantee concerns added
diagnostics, not the entire pre-existing handler.

Before base64 or JSON allocation, a conservative upper bound rejects any event
over the smaller of the remaining queue budget and file limit (512 bytes reserved
for recovery/rotation metadata). The bound includes worst-case control-byte and
Unicode surrogate escaping. This can reject a body whose actual encoded line
would fit; it never saves only part of a body. One accepted event is serialized
at a time in the writer. The queue limit is not total process RSS: temporary
base64/text/JSON objects and Python allocator overhead add bounded working memory
proportional to one accepted event. The pre-existing HTTP read and decompression
buffers remain outside the recorder budget and have not been redesigned.
An event exceeding queue capacity, lock availability or this size bound is discarded
whole and counted as missing; bodies are never silently truncated. The gap is
written at the next successful event, or graceful close. A terminal disk failure
can prevent even the gap marker from reaching disk. Inspect local
`/api/health` → `diagnostics` counters and warning logs as well as files. Sequence
numbers and session IDs let an analyst detect missing events after recovery.

Files are `capture.jsonl` (active) and `capture.1.jsonl` through
`capture.<files-1>.jsonl` (newest to oldest). They rotate before exceeding the
configured file size; default retention is at most 4 × 8 MiB for a capture made
with these settings. This is a rolling window, not an archive: the beginning of
a request or session may be evicted while its later events remain. The first
record in a rotated file marks rotation and whether the oldest file was evicted.
Export before eviction. On first write, existing capture names, link counts,
sizes and indices are checked. Incompatible files (including captures exceeding
new smaller limits) **block recording without growing storage or deleting old
evidence**; inspect `storage_incompatible` and `write_errors` in local health.
Export and clear incompatible evidence privately before reusing that directory.
Existing accepted archive files also receive POSIX owner-only permissions.
Do not change retention settings or externally mutate the private directory
during an experiment. Existing incompatible bytes are not claimed to fit the
new limit; recording stays blocked until the operator resolves them.

Write exceptions never trigger a local fallback or change the cloud result.
Write errors are rate-limited in the log until a successful write. Partial writes
are rolled back when possible; an unterminated tail left by a crash is preserved
on its own line and the next record marks `preceding_unterminated_record`.
Consumers must flag malformed/torn lines rather than silently ignoring them.
No fsync durability guarantee is made: power loss can lose the buffered tail,
including a session-end marker. Graceful close polls for at most one second
without using the shared default executor; the bridge additionally limits the
await to 1.25 seconds. A blocked writer leaves `close_timed_out`/an uncertain
tail; an end-event error sets `end_event_failed`. These diagnostics do not invoke
logging handlers on the event loop. Session-end creation does not prove it was
persisted: require the actual event, counters and gap checks. A fresh session
does not imply a gap-free boundary to the previous session. Failed event
preparation increments bridge `event_errors`; startup failure returns
`startup_failed` and status failure returns `status_failed` in local health.

### Local application, eventual installation and rollback

Current target: existing app `local_braumeister_bridge`, with source at
`/addons/braumeister_bridge`, whose regular 0.3.0 installation and real data flow
have now been checked. Integration 2.0.11-beta is a separate component.
Local diagnostic version **0.3.1-diag.1** is based on app commit
`796d3a9fe7eccca8af5fc21c98b56e8f5cd4bf21`; it is not an upstream release.

Use the cumulative recorder patch only on that pinned baseline in a clean
separate checkout. Run `git apply --check <patch>` before application, then the
supplied regression tests and Ruff. The original diagnostic commits remain in
local history and must not be reapplied to an already patched tree. The supplied
cumulative patch excludes unrelated integration/RTC changes in local history.

See [the preparation and rollback plan](../docs/RECORDER_030_PREPARATION.md).
No recorder deployment or activation is authorized by these local tests.
Before any eventual deployment, preserve a fresh **0.3.0** app backup, source
and options. The older 0.1.4 backup is not the now verified baseline. Review the
currently enabled automatic-update switch before copying a new version file
into the HA source share: that copy itself can make an update available.

Keep existing forwarding/DNS/port/log-level options and persistent `/data`.
After deployment agreement, first run with diagnostics disabled and verify
normal operation. Capture enablement and its restart require separate agreement.
No second app identity on production ports. Rollback should restore only the
freshly saved 0.3.0 app image/data/options and sources, keeping Integration
2.0.11-beta and DNS. Actual restore remains untested.

Private export uses the existing HA app-backup download route for `/data`,
without a new HTTP endpoint or Docker socket exposure. A consistent stopped-app
export is needed: active rotation/copy may leave mixed files or a partial tail.
The synthetic TAR test is not a real Supervisor backup test. Verify the real
export after separately approved installation and before a live experiment.
Select only the app and local storage, and account for automatic backups to
other destinations. Captures remain private.

Begin eventual live observation with 60 passive seconds, no user actions and
unchanged polling. The user handles Chrome; never read sessions or credentials.
Later device actions require individual agreement.

### Local container validation (synthetic only)

`build.yaml` selects `ghcr.io/home-assistant/aarch64-base:3.24` for aarch64.
The Dockerfile requires `BUILD_FROM`; supply it explicitly rather than relying
on the build warning about an empty default argument. For Raspberry Pi 5:

```powershell
docker --context desktop-linux build --load --platform linux/arm64 --build-arg BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.24 --tag braumeister-diagnostics:local-arm64 braumeister_bridge
python tests/container_smoke.py --image braumeister-diagnostics:local-arm64 --platform linux/arm64
```

The helper verifies image architecture and current source hashes, then creates
only its own labeled containers and an internal Docker network. It publishes no
ports, uses no host binds or Docker socket mounts, and performs no runtime
downloads or real endpoint requests. The app reads synthetic options in a tmpfs;
its normal Python entry script is executed. Recorder-off, recorder-on and a
deliberately unusable capture directory must give identical synthetic HTTP
outputs. It checks binary/gzip evidence, error/fallback distinction, request IDs,
explicit oversize gaps and POSIX modes, and removes its container/network IDs in
`finally`. Built images remain review artifacts; no Docker prune is used.

The drop case uses synthetic PUT. aiohttp can internally retry that idempotent
request once; compare the same behavior for all recorder modes. This is inherited
HTTP-client behavior, not a new recorder poll/replay. Actual legacy device POST
semantics and hardware behavior still require separate live evidence. Existing
aiohttp URL canonicalization also remains in place; forwarded wire query text
is not claimed byte-identical to the inbound raw URL in every encoding case.

Report build target and executed architecture separately. Running an arm64 image
as `aarch64` under Docker Desktop on an amd64 engine is an emulated ARM64 test,
not a Raspberry Pi hardware or HA Supervisor integration test.
