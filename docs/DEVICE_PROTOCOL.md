# Braumeister Device ↔ Cloud Protocol

Reverse-engineered from a packet capture of a Braumeister talking to the My Speidel
cloud (Fritzbox packet capture, 2026-10-30, ~5.5 minutes, 281 requests).
Everything marked *hypothesis* is inferred from a single capture and needs confirmation.

Current evidence update (2026-11-02): regular Bridge 0.3.0 and Integration
2.0.11-beta were verified, followed by the optional local 0.3.1-diag.1 recorder.
The passive recorder hardware/export test passed; the recorder is now disabled
and normal forwarding was rechecked. See [the current command experiment
ledger](COMMAND_RE_EXPERIMENTS.md). Historical command mappings below remain
hypotheses until individually correlated browser/cloud/device evidence exists.

Device used for the capture:

| Property | Value |
|---|---|
| Firmware | `V1.1.27 Sep 12 2018` |
| WLAN module | Redpine Signals (MAC OUI `00:23:A7`) |
| Local services | none — all 65535 TCP ports closed/filtered, device is client-only |
| Power saving | WLAN drops off the network intermittently; first ping after idle takes ~250 ms |

## Transport

- **Plain HTTP, no TLS**: `POST http://api2.myspeidel.com/braumeister/connect` (port 80).
- One short-lived TCP connection per request.
- Interval: ~1.2 s on average, up to ~5 s.
- Request body is URL-encoded (`%20` for spaces, etc.); the first `=` separates the
  message type from the payload.
- No DNS query was seen during this initial capture of an already running device.
  The later power-cycle capture documented below established DNS use; re-resolution
  behavior after the TTL expires remains unknown.

## Device → Server

All messages share the same envelope:

```
<type>=<firmware>;<device_id>;<unix_time>;<payload>;<constant>;<signature>
```

| Field | Example | Notes |
|---|---|---|
| `firmware` | `V1.1.27 Sep 12 2018` | |
| `device_id` | `1234567890ABCDEF` | 16 hex chars, the "long UUID" |
| `unix_time` | `1793383969` | Device clock, seconds since epoch (UTC). Previously misnamed `session_id` in the code |
| `payload` | see below | |
| `constant` | 8 hex chars | Same value in every message of one device |
| `signature` | 8 hex chars | Changes per message. Not CRC32/Adler32/MD5/SHA1/SHA256 of any obvious substring — probably keyed. A local server does not need to verify it |

### `bm_stat` — status (sent continuously)

Payload is 19 fields separated by `X`:

```
0X18:12XCX101X-1000X 24.5X4800X82X1X0X0X0X0XEMSRXphX000X0X0X0
```

| Pos | Observed values | Meaning |
|---|---|---|
| 0 | `0` | Display language (MySpeidel `language`; `0` = German). Not used by the integration |
| 1 | `18:12` | Device clock, HH:MM |
| 2 | `C`, `F` | **Temperature unit** as set on the device. With `F`, fields 4 and 5 are in °F (seen live: 33.0 °C → `91.5`, target 40 °C → `1040`); the parser converts them to °C. The recipe list (`rz`) then is in °F too (e.g. mash-in `104`, boil `217`) although it carries no unit itself; it is converted with the unit from the status message |
| 3 | `101`, `2xxx`, `3xxx`, `4006`, `4007`, `6010` | **State / screen code** (see below) |
| 4 | `-1000`, `0`, `380`…`1030` | **Target temperature × 10**; `-1000` = none, `0` between steps (shown as 0 °C, like MySpeidel's web interface). Only meaningful during a program (2xxx/3xxx) or manual mode (4xxx); in menus (101, 8xxx, 6010, 0) it still holds the last program's target – after a °F→°C switch even in °F – and the parser ignores it |
| 5 | ` 24.5` | **Current temperature** in °C (leading space, 0.5 °C steps) |
| 6 | `4800`, `1200`, `60`, `0` | **Duration of the current program step in seconds**: rest (`60` for a 1-min rest), boil (`1200` for 20 min). Outside timed steps it keeps the boil time of the selected recipe. Remaining time = field 6 − field 7 during `2820` (rest) and `3070` (boil) |
| 7 | `0`…`167` | **Seconds since the current state was entered**, resets on state change |
| 8 | `0`…`5` | *Hypothesis:* number of recipe slots synced. Dropped to 0 after `$d=A`, then counted up by one per `$rz` |
| 9 | `0`…`4` | **Recipe slot/index, context dependent.** Historical program captures identify the running recipe. The 2026-11-02 list-navigation captures establish highlighted slots 0 → 1 → 0 and 0 → 3 → 0 in screen `2015`, matching physical positions 1 → 2 → 1 and boundary wraparound 1 → 4 → 1 in a four-slot list. Briefly `4` after entering manual mode; do not interpret it as an active program outside that context. Position 3, other list sizes and empty-list behavior remain untested. |
| 10 | `0`, `5` | Unknown; became `5` at rest end and stayed until the end |
| 11 | `0`, `-1` | *Hypothesis:* hop addition state; changed from `0` to `-1` at the hop addition 10 min before the end of the boil |
| 12 | `0`…`318` | Unknown, counts up during a program (about 3 per minute while boiling) |
| 13 | `EMSR`, `APHT`, `ADUS`, `A000`, `A00F`, `A00S` | Screen/message code (see below) |
| 14 | `ph`, `Ph`, `pH`, `PH`, `qh`, `qH`, `Pi`, `pi` | **Actuator flags**, as read by MySpeidel's own web display (`parseStatus`/`updateScreen` in `bm_controll.min.js`): 1st char pump, 2nd char heater. `P`/`H` = active, `q`/`i` = shown as inactive, `p`/`h` = unmarked. The parser maps `q`/`i` to off. `q` appears during the boil, `i` near the target temperature |
| 15 | `000`, `010`, `0D0`, `00T`, `120` | **Alarm indicator** (middle character): `1` = alarm (mash-in temperature reached, rest end, brew finished), `D` = remove lid (from 99 °C while heating to boil). `00T` while editing the manual-mode target temperature, `120` together with `A00F` |
| 16–18 | `0` | Unknown |

#### State codes (field 3) — *hypotheses*

| Code | Field 13 | Observed context |
|---|---|---|
| `101` | `EMSR` | Main menu / idle |
| `8101`, `8706` | | Settings menu (changing the temperature unit). Entering it pauses a running program (field 15 `120`) |
| `4006` | `APHT` | Manual mode, target 38.0 °C, pump toggled here |
| `4007` | `ADUS` | Manual mode, editing target temperature (38.0 → 39.0) |
| `6010` | `ADUS` | Some sub-menu, entered with `$k=4`, left with `$k=1` |
| `2300` | `A000` | Program started, heating to mash-in (target 40.0 °C), pump cycling |
| `2301` | `A000` | Program, briefly before returning to 101 |
| `2310` | `A000` | Alternates with 2300 (*hypothesis:* pump pause) |
| `2410` | `A000` | Heating to mash-in (pump + heater on) |
| `2510` | `A00S` | **Alarm:** mash-in temperature reached; web step text "… – Einmaischen Temp. erreicht" |
| `2610` | `A00S` | Mash-in temperature reached, waiting for the user to add the malt (seen without beep) |
| `2015` | | Program selected, before the start screen `2030` |
| `2705` | | Briefly after mash-in temperature reached, before the first rest (*hypothesis:* "Malz eingefüllt?" confirmed) |
| `2810` | `A000` | Heating to the next rest (pump + heater on) |
| `2820` | `A00S` | Holding a rest |
| `2930`, `2960` | `A00S` | After rest end, waiting for the user (*hypothesis:* remove malt pipe). Target `0`, pump and heater off, no beep. Follows `2910` once the alarm is confirmed; after the next confirmation the device goes to `3010` |
| `2030` | `ADUS` | Program start screen ("Automatik – <recipe> starten") |
| `2910` | `A00S` | **Alarm:** rest end reached ("Rastende erreicht"), field 15 `010` |
| `3010` | `A00S` | Heating to boil (target 103.0 °C). The pump flag changes from `P` to `q` at about 88 °C (pump switched off for the boil). From 99 °C field 15 is `0D0` = **alarm "Deckel entfernen"** until confirmed |
| `3070` | `A00S` | Boiling; field 7 counts the boil time. Field 11 changes from `0` to `-1` at the hop addition. Hop additions set earlier than the boil time (e.g. 11 and 10 min before the end of a 5-min boil) are skipped: field 11 is `-1` right at the start of the boil, without a beep |
| `3080` | `A00S` | **Alarm:** hop addition ("Hopfen zugeben"), field 15 `010`. The boil timer keeps running; after confirmation back to `3070`. Field 11 counts the hop additions and is `-1` when all are done |
| `3450` | `A00S` | **Alarm:** brew finished ("Brauvorgang beendet"), pump and heater off, field 15 `010` |
| `0` | | Briefly (about 5 s) between confirming "brew finished" and the main menu `101` |

The thousands digit is the program phase: `2xxx` = mashing, `3xxx` = boiling; both count as a
running program. An alarm is active while field 15 signals a beep (`1`/`2`) or the lid (`D`), as in
MySpeidel's own display; `device_protocol.ALARM_STATES` only names it by state code. Codes from
`2410` on come from two live brews where the web interface was polled every 30 s, so short
states can be missed (e.g. the moment of an abort).

After an abort the device goes straight back to `101`. Hop additions are state `3080` with a
beep (seen second-by-second via the Braumeister Bridge; the 30 s web polling missed them).
Field 15 can also be `00Z` for a few seconds during a rest or the boil (meaning unknown).

The heater flag is often `i` near the target temperature and while holding a rest; MySpeidel's display
shows it as inactive. Field 13 `A00S` is not an alarm marker: it holds the labels of the display buttons.

### `rz` — recipe slots (sent on connect / after changes)

The payload starts with the number of slots, then one line per slot (separated by `\r\n`):

```
rz=<fw>;<id>;<time>;5
0X40X44X20X52X20X63X35X73X35X78X10X90X103X90X15X0X0X0X0.Weizen
1X55X55X10X63X45X72X25X78X5X0X0X70X103X60X10X10X0X0X0.Belgisches Gol
...
4X40X40X5X52X20X63X20X73X35X78X20X80X103X60X20X10X0X0X0.NEIPA Nectaron;<constant>;<signature>
```

Each slot line has 20 `X`-separated numbers followed by `.` and the name:

| Pos | Example (Weizen) | Meaning |
|---|---|---|
| 0 | `0` | Slot number (0–4) |
| 1 | `40` | Mash-in temperature °C |
| 2–11 | `44 20 52 20 63 35 73 35 78 10` | 5 rests as (temperature °C, minutes); unused = `0 0` (or `40 0` on the device) |
| 12 | `90` | Boil time, minutes |
| 13 | `103` | *Hypothesis:* boil temperature °C (always 103) |
| 14–19 | `90 15 0 0 0 0` | Hop additions, minutes before end of boil; `0` = unused |

The name is truncated to 14 characters (`Belgisches Gol…`).

## Server → Device

Every request gets an HTTP response with this body:

```
Start\r\n
[$<command>\r\n]
OK\r\n
Done
```

No response signature was identified in the historical capture. This does not
establish the absence of validation inside the firmware, or prove that commands
can be replayed. At most one command per response was observed in that capture.

| Action hypothesis | Context | Browser request | Device command | Reported subsequent device observation | Evidence confidence |
|---|---|---|---|---|---|
| Back key | Screens 4006 / 6010 | Not captured here | `$k=1` | 4006 → 101 / 6010 → 101 | Historical association; full browser-to-device chain unverified |
| Select key / pump toggle | 101 / manual screen 4006 | Not captured here | `$k=2` | 101 → 4006; pump changed inside 4006 | Context-dependent hypothesis; no explicit on/off semantics established |
| Menu key | Screen 101 | Not captured here | `$k=4` | 101 → 6010 | Historical association; screen meaning incomplete |
| Delete/reset recipe slots | Recipe synchronization | Not captured here | `$d=A` | Field 8 fell to 0, then five `$rz` replies | Hypothesis; no isolated delete experiment |
| Write recipe slot | Recipe synchronization | Not captured here | `$rz=<slot line>` | Following `rz` message reported the slot | Historical report; browser mapping and delivery rules unverified |

These rows summarize the existing documentation, not new hardware validation.
The original raw capture is not present in this checkout. Do not promote a row
to a confirmed mapping merely because an HTTP request succeeded or a status
arrived soon afterwards. No new device commands were sent during this analysis.

What a `$k` key press does depends on the screen the device currently shows (field 3).

### Security implications

- Device ↔ cloud traffic is **plain HTTP**: status, recipes and commands can be read by anyone
  on the network path.
- No signature was identified in the captured server response bodies. An attacker
  able to replace plain HTTP responses could attempt command injection; firmware
  validation, replay restrictions and execution conditions have not been established.
- A signature on outbound telemetry alone would not authenticate incoming
  responses. Whether there are additional checks is unknown.
- Authenticated transport or authenticated responses would address response
  integrity; this analysis does not modify or probe firmware validation.

## Relation to the web interface XHR string

The string returned by the My Speidel XHR endpoint is the device's `bm_stat` message,
passed through unchanged:
`firmware;device_id;unix_time;payload;constant;signature`.

It is parsed by `custom_components/speidel_braumeister/device_protocol.py`.
Earlier versions misread it: they took remaining time from pos 6 (a constant, so it always
showed 80 min and "running") and pump/heating from bits of pos 7/8 (a seconds counter and
the recipe count). They also took the recipe slot from field 0 instead of field 9.

### Request and response details

The device sends `Content-Length:` without a space, a static `Authorization: Basic …` header,
`User-Agent: Mozilla/4.0` and `Connection: close`; the body ends with `\r\n `.
The server answers `200`, `Transfer-Encoding: chunked`, `Content-Type: text/plain; charset=UTF-8`,
body `Start\r\n[$command\r\n]OK\r\nDone\r\n`.

## Local integration path

Because the protocol uses plain HTTP, a local bridge can receive and relay the
device's requests:

1. Redirect `api2.myspeidel.com` to a local endpoint (DNS override; the device uses DNS, see below).
2. Answer `POST /braumeister/connect` with `Start\r\nOK\r\nDone` and parse `bm_stat`/`rz`.
3. Optionally forward requests to the real cloud (proxy mode) to keep the app working.

This is implemented by the **Braumeister Bridge** app in `braumeister_bridge/` (see its
`DOCS.md`). The Braumeister's WiFi settings allow a manual DNS server, so only the
Braumeister needs to use the app's DNS server.

## Firmware analysis (public updater package)

Source: `BraumeisterSoftwareUpdater-1.1.27-120918.zip` from the official
[download page](https://www.speidels-braumeister.de/en/service/downloads.html). It contains
the controller firmware `BrewControl-1-1-26.hex` and `BrewControl-1-1-27.hex`, a
`WiFiUpdater.hex` and the flashing tools. The controller is an Atmel AVR (`AVROSP.exe` is
Atmel's programmer). Only the readable strings were examined; nothing was executed or flashed.

- **The device uses DNS (verified).** Both versions contain the Redpine WiFi module commands
  `dnsget=` / `dnsserver=`, the hostnames are stored as text (`api2.myspeidel.com`,
  `firmware.myspeidel.com`), and the server IP does not appear anywhere in the firmware.
  A capture of a power cycle confirmed it: DHCP Discover/Request → ARP for the gateway →
  `A api2.myspeidel.com` to the DNS server from DHCP (the router) → answer `79.99.80.214`,
  TTL 7200 s → first `POST /braumeister/connect` 0.5 s later. The device resolves only
  once when it connects, which is why the earlier capture of a running device showed no
  DNS traffic. A DNS override therefore takes effect after the next power cycle (whether it
  re-resolves after the TTL expires is unknown).
- **Cloud endpoints (1.1.27):** `POST /braumeister/connect` on `api2.myspeidel.com`, firmware
  check `GET /version.txt` and `GET /getfw.php?` on `firmware.myspeidel.com` / `api2.myspeidel.com`.
  1.1.26 used `gaermeister.myspeidel.com` for the firmware check. 1.1.27 added the e-mail
  registration (`Enter Mail:`, `Register`).
- **Local web server:** both versions contain an HTTP server (`ltcp=` = listening TCP socket,
  `HTTP/1.1 200 OK`, `404 Not found`) with these paths:
  `/index.html`, `/bm.html`, `/bm.txt`, `/ui.txt`, `/rz.txt`, `/vs.txt`, plus `image/bmp`
  output (probably a screenshot of the display).
  With 1.1.26 this server was reachable in the local network. The third-party tool
  [speidel-ui](https://gitlab.com/vegard.vesterheim/speidel-ui) uses it:
  - `GET /bm.txt`: status
  - `GET /rz.txt`: list recipes (same format as the `rz` message)
  - `POST /rz.txt` with body `rz=<slot line>`: write a recipe
  - `GET /rz.txt?d=<slot>`: delete a recipe

  With 1.1.27 no TCP port was open on the test device, although the code is still present.
  Its author reports that local access stopped working with 1.1.27. Whether it can be
  re-enabled by a setting is unknown (would need disassembly).
- **Display texts** that match the program steps and alarms: `Wasser eingefüllt?`,
  `Malz eingefüllt?`, `Rastende erreicht`, `Malzrohr entnehmen!`, `Start Hopfenkochen?`,
  `Hopfen zugeben`, `Deckel entfernen`, `Jetzt Whirlpool...`, `Brauvorgang beendet`, `Prost!`,
  `Abbruch`, `Pumpenpause` (supports the 2310 = pump pause hypothesis) and
  `Pumpe wird entlüftet` (supports `q` in the actuator flags = pump venting).

## My Speidel Cloud API (api.cloud.myspeidel.com)

Documented at <https://api.cloud.myspeidel.com/> (OpenAPI 3.0, v1.0; the
v2.0-test spec links return "Cannot GET"). Probed 2026-10-30 with an account that
has a subscription and one Braumeister of the generation described above.

- The server validates every request against the OpenAPI spec. Undocumented
  paths (`/account/machines`, `/machine/{uuid}/status`, which older versions of
  `api.py` used) return `404` just like made-up paths.
- Login: `POST /v1.0/auth/authentication` with `username` and `pass` → bearer token.
- Only timeseries are available (`process`, `phase`, `sensor`, `actor`). There is no
  live-status endpoint and no control endpoint.
- Query values must be URL-encoded (`:` → `%3A`), otherwise `400`.
  `actor` rejects `granularity` (`400 Unknown query parameter`), contrary to the spec.
- Machine IDs: the short numeric ID (the part after the `.`) is accepted. The
  16-hex device ID and the combined form return `404`; IDs longer than 64 characters return `400`.
- **All timeseries were empty** (`200 []`), including the last 24 h, although the
  device had run manual mode and an automatic program a few hours earlier.
  `/account/timeseries/process` is empty too. So data from this device generation
  (firmware V1.x, `api2.myspeidel.com`) does not reach the cloud API.
- The public `/v1.0/firmware` list only contains Linux images for i.MX6UL
  (`image-speidel-swu-imx6ul-var`), i.e. the newer device generation. The cloud API
  is most likely only useful for those devices. This is untested — it needs an
  account that owns such a device.

## Open questions

- DNS use is documented above from firmware strings and a historical power-cycle
  capture; verify the currently deployed routing separately with fresh traffic.
- Remaining unknown fields and state codes: use the field tables above. Several
  older open questions (including field 6) have already been resolved there.
- Full `$k` key mapping, and the meaning of `$d=A`.
- Behaviour during an alarm (e.g. hop addition, "add malt pipe").

## Observation workflow and evidence boundaries

Code audit baseline: upstream `01ac674f4cb35fa04e05708de52b944aebeeadc7`
(2026-11-01). PRs [13](https://github.com/omphteliba/ha-speidel-braumeister/pull/13),
[16](https://github.com/omphteliba/ha-speidel-braumeister/pull/16) and
[17](https://github.com/omphteliba/ha-speidel-braumeister/pull/17) were merged;
[15](https://github.com/omphteliba/ha-speidel-braumeister/pull/15) was open at audit.
That audit did not establish the installed live state. Subsequent user-assisted
inventory, deployment and passive capture have now established it as summarized
above and in the experiment ledger. An integration version is not a bridge version.

The audited bridge routes the configured Host to `handle_device`, reads and
records its application body, then forwards the same body/method/path/query to
the cloud when enabled. It requests identity encoding and decodes supported
compressed cloud replies before writing the answer to the device. A received
HTTP error is relayed; forwarding/read/decompression failures use a local OK
answer. Other Host values follow the separate passthrough path. This is a code
finding, not proof of the current network route.

Current ordinary logging records message types/device identifiers, selected
state changes, `$` command lines and (at debug level) at most 200 response bytes.
`/api/status` keeps the latest payload per message type and the latest response,
not a transaction history. The optional capture described in
[the bridge guide](../braumeister_bridge/DOCS.md#optional-local-diagnostic-capture)
adds full body evidence and per-request correlation without originating commands.

### Manual prerequisites and baseline evidence

Before any deployment, collect the bridge app's installed version, whether it is
local or repository-installed, active options with secrets removed, and startup
plus fresh traffic logs. If source files are visible over an existing share,
record their SHA-256 and `config.yaml` version too, but do not assume that shared
source equals the running container image. Do not install tools, change settings
or restart HA/the app just to collect this evidence.

The owner confirmed completion of the RTC test using integration 2.0.11-beta,
**2026-11-01 23:55 through 2026-11-02 00:05 Europe/Berlin** (22:55–23:05 UTC).
Owner-reported result: OK continuously from 23:55:21 across midnight; 0–1 minute
offset, no day-change jump or false alarm. After switch-off: unknown at 00:05:10,
unavailable at 00:08:01. The owner reports results/screenshots published in PR 15;
these screenshots were not independently re-inspected here. The waiting phase
has ended, but **deployment approval has not been given**. Installation, option
changes and HA/bridge restarts still require agreement on the concrete target,
steps, interruption and rollback. No recorder hardware test has been established
by the successful RTC test.

Using an already available local HA-host shell, sample only the local API:

```sh
date -u '+%Y-%m-%dT%H:%M:%SZ'
curl --fail --silent --show-error http://127.0.0.1:8642/api/health
curl --fail --silent --show-error http://127.0.0.1:8642/api/status
```

Repeat the two API reads manually after approximately 5–10 seconds. This is a
read of bridge memory, not an additional cloud/device poll. Do not expose the
API or change its binding. In a terminal app/container, `127.0.0.1` may refer to
that container rather than the HA host: a connection failure there does not
prove the bridge is down. Use existing host access or supply logs instead.

Keep originals private. In copies, replace device IDs, addresses and signatures
consistently; remove private recipe content. Preserve receipt times, server
`now`, status fields and `last_response_source`. Increasing fresh
`bm_stat_received` demonstrates device requests reaching the bridge. Together
with corresponding fresh forwarding logs and `last_response_source: cloud`, it
supports that this bridge processed a cloud reply. The last source alone has
no independent response timestamp in the old API. Neither that source nor portal
reachability proves delivery or device execution. DNS configuration alone also
does not prove the device used that route.

### Chrome recording (manual only)

1. Sign in yourself. Open DevTools (F12), Network, enable **Preserve log** and
   verify recording is active. Start with Fetch/XHR; if an action has no entry,
   select All and inspect document/other requests and WebSocket messages.
2. Record a 60-second baseline without any portal/device action. Do not change
   polling settings. Separate periodic status reads from action-triggered traffic.
3. For each agreed navigation action, note the exact click time, current portal
   screen and physical display, then perform exactly one action yourself.
   Capture URL/path, method, payload, response status/body and Timing. For a
   WebSocket, record the relevant outgoing/incoming messages and their times.
4. Export the relevant HAR with content, or copy the individual request as cURL
   **for inspection only**. Never execute the copied cURL. HAR sanitization by
   Chrome alone is insufficient: URL/query, payload and response bodies can
   contain tokens, identifiers and recipes. Remove Cookie, Set-Cookie,
   Authorization, account data, tokens in all locations and private recipes
   before sharing. Keep field structure/byte lengths noted when redacting.
5. Preserve bridge timestamps in UTC. On Windows, record
   `[DateTimeOffset]::Now.ToString('o')`, `Get-TimeZone` and `w32tm /query /status`
   in PowerShell (read only). Record HA's configured timezone and UTC host time
   with the local samples. Note Windows/HA NTP synchronization state; browser
   request timing alone does not measure host clock error. If possible record
   Windows UTC immediately before/after an HA-host UTC read to bound clock
   offset by that measurement's round-trip interval. Do not adjust either clock
   during an observation window. Device RTC is a separate clock, not capture time.

### Initial experiment matrix

The bridge-only B00 hardware/export baseline is complete (see the ledger);
browser-side capture and cross-host clock bounds were not collected in it.
Navigation/repetition rows below remain **planned, not performed**. Navigation can be state-dependent;
agree the named control and starting screen before clicking. Do not treat an
unknown portal button as safe based on a guessed `$k` number.

**B00 is the first live experiment, after deployment is separately approved and
the installed route/backup/export prerequisites are evidenced.** Before its
start, the owner signs in manually and prepares DevTools. Do not request or
read credentials, cookies or browser sessions; no automated login or portal
operation is part of this work. Document screen, program state and P/H flags
before T0. Capture the unchanged existing polling for exactly 60 seconds with
no portal/device operation, then record the physical state again at T1. Do not
assume a passive interval contains no spontaneously queued cloud command.

Record T0/T1 in UTC and Europe/Berlin (UTC+01:00 on this date), each host's clock
source and an uncertainty interval for their offset. Use HAR wall-clock start
times plus request durations for browser evidence; use bridge UTC, session,
sequence, correlation IDs and monotonic durations for device exchanges. Cross-
host monotonic values cannot be compared. An apparent match inside overlapping
time uncertainty is a candidate association, not proof. Flag gaps, torn lines,
eviction, incomplete reads and missing end markers before drawing conclusions.
Keep originals private and share only manually sanitized copies. Schedule N01
only after B00 is assessed, and agree that single action separately.

| ID | Starting state | One action | Duration/repetition | Purpose |
|---|---|---|---|---|
| B00 | Stable idle/display documented | None | 60 seconds | Polling baseline, spontaneous messages, clock correlation |
| N01 | Agreed idle main menu, no active program | One agreed menu/navigation control | Observe next status reports for at least 15 seconds | First browser → cloud → bridge → display association |
| N02 | N01 destination documented | One agreed Back/navigation control | Observe at least 15 seconds | Context-dependent navigation; no actuator controls |
| R01 | Same starting state as N01 restored by the user | Repeat precisely N01 once | Separate attempt ID; 15 seconds observation | Identify changing IDs, counters/times and stable command bytes |
| R02 | Same starting state as N02 | Repeat precisely N02 once | Separate attempt ID; 15 seconds observation | Repeatability and state dependence |

For every attempt fill the following record; blanks mean unknown, not absent:

```text
attempt_id:
action_utc / Europe_Berlin / clock_offset_bound:
portal_screen_before / device_screen_before / program_and_actuator_state:
exact_single_action / click_time_precision:
browser_request_id / method / path / sanitized_payload:
browser_status / sanitized_response / websocket_messages_if_any:
bridge_session / correlation_id / cloud_status / raw_command_bytes:
response_source / decompression / response_write_result:
following_status_receipt_times / relevant_status_fields:
physical_display_or_actuator_observation / observation_time_precision:
capture_gaps_or_retention_or_missing_records:
observation / hypothesis / confirmed_mapping / counterevidence:
open_questions / confidence_and_reason:
```

Pump, heater, program start/abort and recipe save/delete are excluded from this
initial matrix. The owner performs such actions only after explicit agreement.
No automated click sequences, replay or production-cloud fuzzing.

### Conditions before future HA control

Require independently repeated, context-specific browser/device mappings and
physical confirmation; distinguish toggle/key semantics from explicit on/off.
Determine parameter syntax/encoding, command ordering in multiline responses,
retries, acknowledgements, duplicates, loss/error behavior and any sequence,
signature or expiry checks. Unknown fields remain unknown. Assess safe state
preconditions and recovery separately. The current patch adds no control API,
automatic replay or extra cloud polling. Its synthetic tests establish capture
and forwarding behavior only, not real command meanings.
