# MySpeidel command RE – evidence ledger

Updated 2026-11-02. No HA control interface, replay or automated device command.
Raw evidence remains in private local archives outside Git. This ledger contains
only public protocol bytes and aggregate observations; no IDs, recipes or sessions.

## Current verified setup

- Existing local app: Bridge 0.3.1-diag.1, prepared commit 607b25b, based on the
  0.3.0 app from 796d3a9. Integration 2.0.11-beta now reads fresh Bridge data.
- Recorder hardware capture, clean SIGTERM shutdown and actual HA backup export
  verified. Recorder subsequently disabled; health OK and fresh cloud-sourced
  status rechecked. No recorder or HA changes authorized by this document alone.
- Bridge automatic updates off. Bridge excluded from automated backups to prevent
  private captures being sent to external destinations. Keep that exclusion while
  raw captures remain in app data; no capture deletion has been performed.
- Backup/source and private export routes are established; restore remains untested.
- Every new physical/portal action is agreed individually with the owner.

## B00: bridge-only passive baseline, complete

Session duration: 64.938286 s, including startup/shutdown margins around the
requested 60-second observation. 450 contiguous events, one start and one end,
56 complete correlated exchanges, HTTP 200, no gaps/error/fallback events.
All requests were POST `/braumeister/connect`.

Every raw cloud entity and intended outgoing response was exactly 17 bytes:

```
Start\r\nOK\r\nDone\r\n
```

No `$` command lines, compression or non-text bodies occurred. Base64/Latin-1/
length checks passed for all 168 body records. This establishes an observed
command-free reference, not a guarantee that future passive periods contain no
queued commands. Unchanged recipe-file hash and expected options were verified.

Request-start spacing in this capture: min 1.006 s, median 1.024 s, max 3.704 s.
Cloud-request-start to complete-entity-read: min 53.9 ms, median 63.1 ms,
max 133.1 ms. These are application observations, not packet-level timings or
pure server execution time. No polling changes were made.

Browser traffic and cross-host clock offset/uncertainty were **not recorded**.
Consequently B00 does not establish the browser-to-cloud part of the chain.
For the next session collect a new passive browser baseline before the action.

## Existing command evidence

### N01 observed once; final stopped export verified

The owner performed the approved single main-menu Manual click. A browser
screenshot shows GET `/braumeister/setDeviceStatus/<DEVICE>.<SHORT_ID>/k/2`,
HTTP 200. Its cloud Date header is 2026-11-02 16:50:00 UTC; an exact browser
click timestamp was not supplied, and that header is not a click-time measurement.

The first private N01 export contains exactly one command line, **`$k=2`**,
received from the cloud at **16:50:02.862648 UTC**. The associated device request
reported **101/ph**. The response writer completed at 16:50:02.863246 UTC;
the next recorded bm_stat reported **4006/ph** at **16:50:04.402480 UTC**,
1.539 s later using the bridge monotonic clock. P/H flags stayed ph. The owner
independently confirmed the real device display showed **Manueller Betrieb**.
This supports the mapping for one main-menu observation, not an unconditional
meaning for key 2 on other screens. Independent repetition remains outstanding.

The exported N01 snapshot spans 16:45:12.598848–17:35:37.167226 UTC,
**50 min 24.568 s**, because recording continued beyond the intended short
window while the owner was away. It contains 23185 contiguous events and
2898 complete cloud exchanges, all HTTP 200; 2897 ordinary 17-byte acknowledgments
and one command response. All 8694 body representations validate and the raw/
decoded cloud-to-device bodies match. No error/gap/fallback event was found in
that snapshot; recipe-file hash is unchanged.

Real rotation occurred: one retained archive below 8 MiB and one active file,
both 0600. The earlier B00 prefix remains byte-identical. No retained beginning
was evicted in this export. However N01 has **no session_end**: this is an active
snapshot, not a proved clean final session. The owner has now confirmed the
Bridge is stopped. That first snapshot has been preserved.

The subsequent stopped-app export is now verified: **27522 contiguous N01
events**, exactly one session_start and one session_end; **3440 complete Cloud
exchanges**, all HTTP 200. It retains every capture byte from the first export,
the B00 prefix and unchanged recipes. All 10320 body records validate. The session
ends at **17:45:28.864953 UTC**, after **60 min 16.266 s** overall. No eviction,
gap, malformed tail or recorded read/write/forwarding error was found. This was
an extended AFK recording, not a precisely bounded 75-second trial.

The only command response contains this 23-byte device-response envelope:

```
Start\r\n$k=2\r\nOK\r\nDone\r\n
```

Its correlation and timestamps match the first snapshot exactly. The other 3439
exchanges carry the ordinary 17-byte acknowledgment. This closes the evidence
set for a single context-specific N01 observation. Precise browser click timing,
independent repeatability and other screen contexts remain outstanding.
N01 recovery was confirmed: recorder disabled, health OK, fresh cloud-sourced
status approximately 1.59 seconds old. N02 was then separately approved below.

### N02 observed once; final stopped export verified

The owner separately approved exactly one MySpeidel **Abbruch** click from
Manual, after confirming the physical Manual display, both actuators off and no
brewing program. A fresh recorder session and passive baseline preceded it.
The owner screenshot shows GET
`/braumeister/setDeviceStatus/<DEVICE>.<SHORT_ID>/k/1`, HTTP 200, and the main
menu. The owner confirmed the real display also returned to Hauptmenue, with
pump and heater off. The browser Date header is 18:09:28 UTC; precise click time
was not supplied and is not established by that header.

The stopped-app export contains **3034 contiguous events**, one session_start
and one session_end, from **18:06:12.089399 to 18:12:51.451614 UTC** (399.362 s).
All **379 complete cloud exchanges** returned HTTP 200. All **1137 body records**
pass Base64/Latin-1/length validation; decoded cloud entities match outgoing
bodies exactly. No gap/error/fallback event or malformed tail was found. No
rotation or eviction occurred in N02; every capture byte from the final N01
export, the B00 prefix and the recipe-file hash remain unchanged.

Exactly one cloud reply contained **`$k=1`**, received at **18:09:29.464717 UTC**
and written completely at **18:09:29.465309 UTC**. Its 23-byte envelope was:

```
Start\r\n$k=1\r\nOK\r\nDone\r\n
```

The associated device request reported **4006/ph**. The first following bm_stat
reported **101/ph** at **18:09:31.400169 UTC**, **1.93485228 s** after write
completion using the Bridge monotonic clock. All other 378 replies were ordinary
17-byte acknowledgments. Flags stayed ph throughout the session. The omitted
post-action terminal status is therefore covered by recorded device telemetry.
This establishes one Manual-to-main-menu observation, not universal key-1
semantics, independent repeatability or a precise browser-to-device latency.

The app is stopped after export; recorder disablement and normal recovery are
pending. No further navigation, actuator action or recipe operation is approved.

### Four-action menu block; final stopped export verified

After N02 the owner requested continuous recording across multiple individually
approved actions. Recorder disablement between actions is not required. The
owner approved Settings, Settings Cancel, Recipe and Recipe Cancel separately;
no values, recipes or actuators were edited. Every resulting physical display
was confirmed by the owner. Recorder health before closing reported 7937/7937
events, no drops or errors. The final stopped export was validated offline.

Session **18:40:25.144863–18:58:23.137547 UTC**, 1077.992684 seconds:
**8298 contiguous events**, one start and one end, **1037 complete cloud
exchanges**, all HTTP 200. Exactly four responses contain one key command each;
the other 1033 contain the ordinary 17-byte acknowledgment. All **3111 body
records** validate as Base64/Latin-1/length; decoded cloud entities equal outgoing
device-response bodies. Every command response is the 23-byte envelope
`Start\r\n$k=N\r\nOK\r\nDone\r\n`. No gap, malformed tail, fallback or
recorded read/write/cloud error was found.

| Approved action | Browser suffix | Cloud command | Cloud received (UTC) | Device state | Write completion to next bm_stat |
|---|---|---|---|---|---|
| Main menu → Settings | /k/1 | `$k=1` | 18:42:42.814396 | 101 → 8101 | 1.306500 s |
| Settings → main menu (Abbruch) | /k/1 | `$k=1` | 18:46:53.393974 | 8101 → 101 | 1.950302 s |
| Main menu → recipe list | /k/4 | `$k=4` | 18:51:12.760234 | 101 → 6010 | 1.894415 s |
| Recipe list → main menu (Abbruch) | /k/1 | `$k=1` | 18:54:51.405799 | 6010 → 101 | 1.982641 s |

All browser entries are owner-observed GET requests with HTTP 200. Flags remain
ph throughout the recorded state sequence. Latencies above use only the Bridge
monotonic clock; precise browser click timestamps and independent cross-host
latency measurements remain unavailable. Each mapping has one isolated
observation in this block, not proof of universal key semantics or repeatability.

The real Settings screen exposes the full settings menu; the real Recipe screen
shows the recipe list. MySpeidel instead renders notice pages in those contexts.
Do not infer the physical menu contents or allowed operations from those portal
notices. No setting or recipe modification was performed.

Rotation produced three retained files, each below 8 MiB with mode 0600. No
oldest file was evicted. Every capture byte from the N02 final export, including
the B00/N01 evidence, is retained; recipe-file hash remains unchanged. The
private archive and detailed correlation/hash report remain outside Git.

At export completion the Bridge is stopped. The owner-approved continuous
recording workflow allows keeping diagnostics enabled when restarting for the
next block; no next menu/device action is approved by this ledger. Restore and
verify Bridge operation before a new action. Export before rotation can evict
unexported evidence; automatic external backups remain excluded.

### Braustart to recipe selection and Cancel; stopped export verified

The owner explained that main-menu key 3 first opens recipe selection, then
separately approved one Braustart click only up to that screen. The owner later
separately approved one Cancel click back. No recipe was selected, no brewing
start was confirmed. Both physical screens and both browser GET/HTTP-200 entries
were confirmed. This observes navigation on this device, not a general guarantee
that every firmware/context interprets the key identically.

The final stopped session spans **19:27:49.157714–19:50:57.893311 UTC**,
1388.735597 seconds. **10586 contiguous events**, one start and one end,
**1323 complete cloud exchanges**, all HTTP 200. All **3969 body records** pass
Base64/Latin-1/length checks; decoded cloud entities equal outgoing device bodies.
Exactly two 23-byte key-command envelopes occur; the other 1321 responses are
ordinary 17-byte acknowledgments. No gap, fallback, malformed tail or recorded
read/write/cloud error was found. The pre-stop health sample reported 9817/9817
events with no errors/drops; additional events were captured before clean stop.

| Approved action | Browser suffix | Cloud command | Cloud received (UTC) | Device state | Write completion to next bm_stat |
|---|---|---|---|---|---|
| Main menu Braustart → recipe selection | /k/3 | `$k=3` | 19:38:01.249058 | 101 → 2015 | 1.050967 s |
| Recipe selection Abbruch → main menu | /k/1 | `$k=1` | 19:46:46.542250 | 2015 → 101 | 1.946505 s |

Flags remain ph throughout. The Bridge monotonic delays are not browser-click
latencies; only second-resolution cloud Date headers were supplied for browser
timing. Each transition is observed once. Recipe browsing within 2015, selection,
confirmation and actual program start remain untested and unapproved.

No rotation or eviction occurred in this session. All capture bytes from the
previous menu-block export are preserved, including earlier B00/N01/N02 evidence;
recipe-file hash is unchanged. Three files remain below 8 MiB each with mode
0600. Current retained capture size is 23230200 bytes. Future continuous sessions
can eventually evict the oldest file under the configured four-file retention;
preserved private exports remain the independent evidence copies. The app is
stopped after export; restart/health verification precedes any further experiment.

### Recipe-list navigation and repeated entry clicks; stopped export verified

The owner approved the complete list-navigation test: enter recipe selection,
Down, Up and Cancel, with no selection confirmation, editing or program start.
During entry the owner reported a portal hang and clicked Braustart three times
before both displays changed. A screenshot shows three new /k/3 entries, but
only the last entry's HTTP 200 and Date header are evidenced in detail. Treat
this entry as a deviation from an isolated single-click experiment. After the
physical list position 1 remained stable for at least 15 seconds, one Down and
one Up moved both portal and physical-device highlights 1 → 2 → 1; one Cancel
returned both displays to the main menu.

The stopped export contains the complete session **19:57:51.770504–20:58:29.770388
UTC** (3637.999884 seconds): **27394 contiguous events**, exactly one start and
one end, **3424 complete cloud exchanges**, all HTTP 200. All **10272 body
records** pass Base64/Latin-1/length checks; decoded cloud bodies equal intended
outgoing device bodies. Exactly four 23-byte command envelopes occur; 3420
responses are ordinary 17-byte acknowledgments. No gap, malformed tail,
fallback or recorded read/write/cloud error was found. Pre-stop health reported
26929/26929 events, no errors/drops. Flags stay ph throughout.

| Action/context | Browser suffix | Observed cloud command | Cloud received (UTC) | Following telemetry | Write completion to next bm_stat |
|---|---|---|---|---|---|
| Enter from main menu after three owner clicks | /k/3, three entries | `$k=3`, once for entry | 20:04:59.867209 | 101 → 2015, field 9 = 0 | 1.031459 s |
| Down in recipe selection | /k/2 | `$k=2` | 20:49:24.736472 | 2015, field 9: 0 → 1 | 0.531337 s |
| Up in recipe selection | /k/3 | `$k=3` | 20:52:36.884263 | 2015, field 9: 1 → 0 | 0.556117 s |
| Cancel to main menu | /k/1 | `$k=1` | 20:55:49.631560 | 2015 → 101 | 1.967238 s |

In this screen, field 9 therefore tracks the zero-based highlighted recipe slot
for the two observed positions; it is not restricted to a running program.
List boundaries, wraparound, other slots and selection confirmation remain
untested. No recipe-file change occurred.

The full entry-to-exit capture contains only one entry key-3 reply plus the later
Up key-3 reply. It does not show three device deliveries for the three entry
clicks. The first two browser results/timings and cloud-side queue internals are
unknown. Do not conclude deduplication, lost packets, timeout cause, or that
repeating a key is safe. Bridge-local monotonic delays above do not establish
browser-click latency; exact click times were not supplied.

Actual rotation evicted the oldest retained file: B00 and an early part of N01
are no longer in this current app export. The other two file prefixes from the
previous recipe-selection export remain byte-identical. All four current files
are below 8 MiB with mode 0600, total 27625711 bytes. The current session itself
is complete from sequence 1. Earlier private exports remain preserved as the
evidence copies; do not describe this current export as retaining all history.

The Bridge is stopped after export. Continuous recording may resume after start
and health verification. No additional device action is authorized here.

### Four-slot list boundaries; stopped export verified

The owner approved entry, both boundary-navigation actions and Cancel, excluding
selection confirmation or program start. Both portal and physical device showed
position 1 of 4 after entry, position 4 after one Up, position 1 after one Down,
and the main menu after Cancel. Each browser request is owner-observed GET with
HTTP 200; no repeated-click anomaly was reported in this block.

The stopped session spans **21:05:11.605179–21:16:06.222159 UTC** (654.616980 s).
**5426 contiguous events**, one start and one end, **678 complete cloud exchanges**,
all HTTP 200. All **2034 body records** pass Base64/Latin-1/length validation;
decoded cloud bodies equal outgoing device bodies. Four 23-byte key-command
envelopes occur, with 674 ordinary 17-byte acknowledgments. No gap, malformed
tail, fallback or recorded cloud/read/write error was found. Pre-stop health
reported 4993/4993 events with no drops/errors. Flags remain ph throughout.

| Action | Browser suffix | Cloud command | Cloud received (UTC) | Following telemetry | Write completion to next bm_stat |
|---|---|---|---|---|---|
| Entry | /k/3 | `$k=3` | 21:07:06.803066 | 101 → 2015; field 9 = 0 | 1.080778 s |
| Up at first position | /k/3 | `$k=3` | 21:09:33.434914 | 2015; field 9: 0 → 3 | 0.522833 s |
| Down at last position | /k/2 | `$k=2` | 21:11:25.166838 | 2015; field 9: 3 → 0 | 0.528953 s |
| Cancel | /k/1 | `$k=1` | 21:13:43.100409 | 2015 → 101 | 2.002351 s |

This establishes wraparound in both directions for the observed four-slot list,
not behavior for every firmware, list size or empty list. Field 9 is confirmed
as the zero-based highlighted slot for observed positions 1, 2 and 4 across the
two navigation blocks. Position 3 and selection confirmation remain untested.
Delays use only the Bridge monotonic clock; exact browser-click timing remains
unavailable. Browser Date headers must not be used as click timestamps.

No rotation or eviction occurred in this session; all bytes retained in the
previous recipe-navigation export remain present as file prefixes. Earlier
history already evicted before this session remains in the separate private
exports, not this running retention set. Recipes are unchanged; four retained
files remain below 8 MiB each with mode 0600. The app is stopped after export;
restart and health verification precede any further action, which requires its
own agreed scope. No recipe selection, editing or actual brewing was performed.

### Static frontend evidence, 2026-11-02

User supplied `bm_controll.min.js`, 36490 bytes, SHA256
`dd70cc24fb772d3e32791d2d0ff9c1f1a18d1b5c8ac3f888034c91021d0bb5fb`.
Read as source only, never executed. Read-only Chrome inspection independently
found these visible main-menu list items; no portal button was clicked:

| Label | DOM id | Static navigation class |
|---|---|---|
| Einstellungen | settings | display-content-navigation-button-1 |
| Manuell | manually | display-content-navigation-button-2 |
| Braustart | brewstart | display-content-navigation-button-3 |
| Rezept | recieps | display-content-navigation-button-4 |

The file registers delegated `.dbutton` and `.bmbutton` click handlers. Each takes
the selected element's zero-based sibling index plus one as key number, while
respecting the disabled class and screen-dependent branches. For a main-menu
`.dbutton` with state below 1000, key 2 calls `setBmStatus(2, true, false)`.
Together with the observed second main-menu item, this establishes the **frontend
dispatch candidate** for Manual. It does not independently establish what the
cloud queues or the device executes.

`setBmStatus(e,t,r)` builds:

```javascript
typ = "k";
// static structure; do not execute as a live probe
url = bmaction + "/" + typ + "/" + e;
// $.ajax: method GET, data "", timeout callTimeout, async r
```

Its success callback resets its retry counter and passes the returned body to
`getCurrentBMStatus`. Failure increments the counter and retries at 600 ms while
the incremented value is below 10: up to 10 attempts total for that failure chain.
The arguments are saved in shared `setBMStatusFunctionVars`; do not assume
concurrent actions have independent retry state. No retry was deliberately
triggered. A control operation encoded as GET is still state-changing; do not
open or replay a candidate URL to discover its meaning.

The file defines `shortterm=3000` and `callTimeout=4*shortterm` (12000 ms).
Recurring browser XHRs have been manually observed as GET
`/braumeister/getDeviceStatusControl/<DEVICE>.<SHORT_ID>` with HTTP 200.
These are browser/cloud status requests, distinct from device POSTs to
`/braumeister/connect`. No additional status poll was generated by inspection.

Temperature and time setters use separate base variables and may follow a
successful edit with key 4 when the response JSON says `nextToDo=closeEdit`.
Recipe-selection branches also exist. This demonstrates why one UI action can
produce multiple requests and why keys must be interpreted in their screen
context. These controls remain excluded from initial experiments.

The controller file **uses but does not assign** `bmaction`, `bmstat`,
`bmvers`, `bmtempaction` or `bmtimeaction`. A targeted read of inline script text
in the existing control page found no literal assignments either. Do not invent
the missing control-endpoint base or claim the full browser-to-command mapping.
The next observed source, `/assets/javascripts/views/braumeister/functions.min.js`,
has now also been supplied as `myspeidel-bm-functions.min.js`: 1951 bytes,
SHA256 `fa5fc9f3082410dcb922820faddfb4bec9f2dfa15738483257d41d12f09b39a9`.
It contains hover/current-selection classes, recipe-list expansion/selection,
information-panel toggles and Cancel-event forwarding, but no Ajax call or URL
base definitions. Cancel forwards a click to `.display-content-navigation-li.cancel`;
that can reach a handler in the controller file, so it must not be interpreted
as necessarily cosmetic. The source was never executed during this inspection.

Chrome Sources global search found only the known controller usage. The owner
then manually read the existing `bmaction` string in DevTools Console (no setter
or function call). The supplied screenshot establishes its sanitized value:

```
https://www.myspeidel.com/braumeister/setDeviceStatus/<DEVICE>.<SHORT_ID>
```

Combining this runtime string with the static builder establishes the expected
main-menu Manual request form:

```
GET /braumeister/setDeviceStatus/<DEVICE>.<SHORT_ID>/k/2
data: "" (no explicit Ajax payload)
```

This is not an observed live action request. It does not establish server queueing,
delivery timing, expiry, duplicate handling, authorization design or the exact
device command by itself. The source assignment location is still unknown, but
the current endpoint value is no longer guessed. No request to this action URL
was made by the agent; no portal control was clicked during inspection. The
owner's GET status poll remains `/braumeister/getDeviceStatusControl/...` and
must not be confused with this state-changing GET route.

Keep device identifiers private. Never inspect cookies or credentials,
execute setters, or probe/replay the derived control URL. Next evidence must be
one separately agreed owner action captured in Browser and Bridge together.

| Candidate | Available evidence | Still missing |
|---|---|---|
| Main menu → Manual: `$k=2` | N01: observed browser GET /k/2, one correlated cloud reply, subsequent 101/ph → 4006/ph and owner-confirmed physical Manual display; final stopped export verified. | Precise browser click-time evidence, independent repetition; other screen contexts remain unknown. |
| Manual → Main menu: `$k=1` | N02: one approved Abbruch click, browser GET /k/1, correlated cloud reply, 4006/ph → 101/ph, physical main menu confirmed; final stopped export verified. | Precise click timestamp, independent repetition and other screen contexts. |
| Main menu → Settings; Settings → main menu: `$k=1` | Four-action block: browser /k/1, correlated cloud replies, 101/ph → 8101/ph → 101/ph; physical screens confirmed. | Independent repetition; other screen contexts. |
| Main menu → recipe list: `$k=4`; Cancel: `$k=1` | Four-action block: browser requests, correlated cloud replies, 101/ph → 6010/ph → 101/ph; physical recipe list/main menu confirmed. | Independent repetition; recipe selection/editing not tested. |
| Main menu Braustart → recipe selection: `$k=3`; Cancel: `$k=1` | Separate stopped export: browser requests, correlated cloud replies, 101/ph → 2015/ph → 101/ph; physical screens confirmed. | Independent repetition; selecting/confirming a recipe or starting a program not tested. |
| Recipe selection Down/Up: `$k=2` / `$k=3` | Complete navigation and boundary exports: correlated cloud replies and physical highlights 1 → 2 → 1 and 1 → 4 → 1; field 9: 0 → 1 → 0 and 0 → 3 → 0, state 2015/ph unchanged. | Position 3, other list sizes, independent repetition; earlier entry's three clicks remain an unresolved anomaly. |
| `$d=A`, `$rz=...` recipe operations | Historical association only. | Isolated semantics and browser mapping; excluded from initial navigation study. |

`$k` is treated as a context-dependent key candidate, not an explicit actuator
on/off API. In the manual screen the same key may have an actuator meaning.
Do not derive an unconditional "pump on" command from the number alone.

## N01 agreed procedure (performed; final export verified)

Approved scope: start at idle main menu, both P/H off, no active program. One manual
click by the owner on **Manuell** in MySpeidel; observe at least 15 seconds after
it. No pump/heater/temperature/program/recipe controls. Returning is N02 and
requires separate agreement; no automatic click sequence or replay.

Preparation order:

1. Owner opens Chrome DevTools Network, Preserve log, initially Fetch/XHR, while
   already signed in. No credentials/session/cookies are requested or inspected.
   Observe periodic requests before choosing the action entry. If no relevant
   entry exists, inspect request types manually, including WebSocket if present.
2. Record current portal and physical display, program/P/H status. Check clocks:
   Windows and HA UTC, synchronization source and uncertainty. Keep wall-clock
   comparisons uncertain until the bound is established; do not adjust clocks.
3. After separate agreement of N01 and its single control, enable a fresh recorder
   session with the existing options, log_level info and unchanged polling. Confirm
   writer health. Note that existing B00 files remain; distinguish by session/seq.
4. Record at least 60 s passive browser + bridge baseline. Then the owner performs
   exactly the agreed single click and notes its time. No subsequent action.
5. Record method/path, sanitized payload structure, status and timing for the
   browser action. Never supply full request headers, Copy-as-cURL commands,
   session identifiers, cookies, authorization or unreviewed HAR. Body/query tokens
   may also be sensitive: owner redacts them before sharing. Original stays local.
6. Close capture cleanly, export only locally through the proven route, disable
   recorder and restore normal forwarding. Extract only bridge capture members
   for analysis; a full HA export may also contain HA/SSL and stays private.

Evidence record: exact named action and starting screen; click time/uncertainty;
sanitized browser method/path/payload/response and request ID; bridge session,
sequence/correlation and exact raw command; following status/state/flags; owner
observation of the physical display. Keep request acceptance, response writing
and actual device effect distinct. A timely HTTP 200 alone proves none of the
command meaning or device execution. Flag missing/gapped evidence explicitly.

N02, the four individually approved menu-block actions, and opening/cancelling
the Braustart recipe-selection screen are performed as recorded above. Selecting
a recipe, editing it, confirming a program start, actuator actions and other menu
actions remain unperformed and unapproved. Firmware
validation, replayability, signatures, queueing, duplicate
delivery and multi-command ordering remain unknown.

Identifier correction: the integration README documents the suffix as the short
device ID from `/braumeister/control/<SHORT_ID>`, not an established account ID.
Earlier `<ACCOUNT>` placeholders in this ledger referred to that suffix and
were misleading. The combined device identifier remains `<DEVICE>.<SHORT_ID>`.
The owner reports email-based account binding without a device password; no
portal authorization or credential mechanism was tested or inferred from that.
