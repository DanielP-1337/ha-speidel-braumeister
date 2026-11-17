# Water prompt / possible delayed-start screen, 2026-11-17

Source: user-supplied JSONL attachment f64f26ab-e2a3-4389-a360-b5e5c80c226b,
same session as the manual-editor trial. User reports two Up, two Down, one Up,
then Abort, with no lead-time display. Final screenshot shows the main menu.

The recorded cloud responses contain more Up commands than the initial reported
click sequence. The user subsequently clarified that additional double-click
attempts explain all six Up commands; single and double clicks made no visible
difference. This capture is not evidence of unintended cloud repetitions.

| CET | Record | Key | Incoming state | First subsequent status |
|---|---|---|---|---|
| 22:40:49.679 | 1514 | 3 | 2030 | 1516: 2111 |
| 22:40:59.204 | 1546 | 3 | 2111 | 1548: 2111 |
| 22:41:13.128 | 1582 | 3 | 2111 | 1584: 2111 |
| 22:41:26.274 | 1617 | 2 | 2111 | 1619: 2111 |
| 22:41:36.137 | 1649 | 2 | 2111 | 1651: 2111 |
| 22:41:42.944 | 1676 | 3 | 2111 | 1678: 2111, another key 3 response |
| 22:41:43.567 | 1678 | 3 | 2111 | 1680: 2111 |
| 22:42:11.495 | 1723 | 3 | 2111 | 1725: 2111 |
| 22:42:18.244 | 1750 | 1 | 2111 | 1752: 101 / EMSR / 000 |

The first Up changes state 2030 to 2111. All subsequent arrows retain 2111,
ADUS and 000. Target field 4 remains 380, duration field 6 remains 300;
field 7 advances with time and is not evidence of a selected delay.
No active pump/heater flags are observed (ph). Abort returns to the main menu.

This confirms command delivery and a state transition, not a working delay
value or its increment. No delay value can be identified from these recorded
fields. It remains possible that a value is visible only on the physical display
or carried outside the sanitized fields (field 1 and raw non-status messages
are not recorded). The current evidence does not establish that arrows are
ineffective or that the function is unavailable through MySpeidel.

Next useful observation: compare the physical display and cloud display after
one Up from the water prompt, without Select/start confirmation. If a value
appears on the physical device, capture its before/after values and timestamps.
The extra Up responses are explained by the user's subsequent double-click
clarification above.

## Physical-device follow-up

User reports pressing Up, Down, Abort directly on the device. Read-only review
of the live share shows the following status transitions in the same session:

| CET | Sequence | State / fields 13 and 15 | Observation |
|---|---|---|---|
| 22:48:52.457 | 2147 | 2015 / ADUS / 000 | Recipe selection |
| 22:48:55.502 | 2149 | 2015 / ADUS / 000 | Recipe index changes 0 -> 1 |
| 22:48:57.066 | 2150 | 2030 / ADUS / 000 | Water prompt, target 380 |
| 22:49:01.146 | 2154 | 2111 / ADUS / 000 | Same state transition observed with cloud Up |
| 22:49:29.206 | 2178 | 0 / ADUS / 000 | Intermediate status on exit |
| 22:49:32.289 | 2179 | 101 / EMSR / 000 | Main menu |

There are no key commands in these listed records, consistent with physical
operation. Source `cloud` identifies the response route, not the origin of a
physical press. Target 380 and duration 300 remain unchanged after entering
the water prompt; actuator flags remain ph. No separate Down transition is
identifiable from the recorded fields. The timestamp for Down cannot be
assigned reliably. Device-display content during 2111 still needs user
confirmation: the user's message describes the presses, not the shown value.
No conclusion about the availability or increment of delayed start is warranted.

## Cloud commands with simultaneous physical-display observation

The user subsequently observed the BM display while operating MySpeidel:
Up adds 30 minutes, Down subtracts 30 minutes, and Abort exits. The physical
device accepts the cloud commands like its own buttons, while the web page
does not display the selected delay. This establishes the observed increments
from the user's display observation, not from a decoded numeric status field.

| CET | Command record | Command | First subsequent status |
|---|---|---|---|
| 22:52:30.505 | 2373 | Up `$k=3` from 2030 | 2375: 2111 / ADUS / 000 |
| 22:52:34.753 | 2390 | Down `$k=2` from 2111 | 2392: 2111 / ADUS / 000 |
| 22:52:44.355 | 2422 | Abort `$k=1` from 2111 | 2424: main menu 101 / EMSR / 000 |

All three are cloud responses with HTTP 200; listed status flags are ph.
The sanitized numeric fields still do not expose an identifiable delay value.
The exact cause of the missing web display is unverified (rendering versus
data not provided to the web UI). Do not infer the delay by counting key
presses: limits, repeats, initial values and other control paths are untested.
Start confirmation/countdown behavior is still untested.

Rotation integrity check: previous file contains 2330 valid JSON records,
sequences 1..2336; current file at inspection contains 345 valid JSON records,
2337..2681. Same session, contiguous rotation boundary 2336 -> 2337.
The current file has no sequence gaps; this latest test is fully captured.
The previous file has six missing sequence numbers (396, 421, 858, 859,
1807, 2254), so the entire historical session is not gap-free.
Both export files were copied to the local `captures/2026-11-17-start-delay`
folder to preserve the evidence before further rotation.

## Confirmation and countdown: field 17 identified

User subsequently pressed Up twice and Select, and supplied a MySpeidel
screenshot showing 'Beginn in 0 h 59 min' and 'Braustart um 0:00 Uhr'.
The web UI therefore DOES display the countdown after confirmation; the
previously missing display concerns the selection stage, not all delay states.

| CET | Sequence | Observation |
|---|---|---|
| 23:00:15.549 | 2917 | Cloud `$k=3` in 2030 |
| 23:00:16.148 | 2919 | 2111 / ADUS / 000 |
| 23:00:22.673 | 2946 | Cloud `$k=3` in 2111 |
| 23:00:28.971 | 2971 | Cloud `$k=4` in 2111 |
| 23:00:30.515 | 2973 | 2120 / A00S / 000, field 17 = 3599 |
| 23:02:10.091 | 3025 | 2120 / A00S / 000, field 17 = 3499 |

Field 17 decreases by 100 seconds over approximately 100 seconds of wall time.
Together with two observed +30-minute selections and the screenshot, this
identifies field 17 as remaining delay seconds in state 2120 for this firmware.
Field 6 remains 300, and field 7 continues its unrelated elapsed count; neither
is the delay countdown. Actuator flags in the observed countdown are ph.
Field 13 A00S matches Abort and Select with the middle two buttons absent.

The countdown snapshot is saved as
`captures/2026-11-17-start-delay/diagnostics-countdown.jsonl`.
The actual zero-expiry behavior, Select while already counting down, and
Abort from 2120 have not been established by this capture. Do not generalize
field 17 to other states or interpret the page's displayed midnight as a
separately decoded timestamp. No control commands were issued during analysis.

## Countdown Abort confirmed

User reports cancellation and supplies a main-menu screenshot. The log shows
cloud `$k=1` at 23:03:52.732 CET, record 3057, in state 2120 / A00S / 000
with field 17 = 3397. The next available status, record 3059 at 23:03:54.822,
is main menu 101 / EMSR / 000 with field 17 reset to 0. Actuator flags remain
ph. The last status inspected, record 3151, still shows main menu and zero
remaining delay. Thus Abort from the active countdown cancels the delayed
start and returns to the main menu in this trial. Select during countdown and
expiry at zero remain untested. Snapshot preserved as
`captures/2026-11-17-start-delay/diagnostics-countdown-abort.jsonl`.

## HA beta hardware validation

User tested the coordinated HA beta through the Display Card and compared it
with MySpeidel. Both Up commands, confirmation and countdown Abort have source
`local_control`, confirming the HA/Companion/Bridge path rather than cloud keys.
Sequence numbers below belong to the new session after the Bridge restart.

| CET on November 17 | Command record | Action | Next status |
|---|---|---|---|
| 23:53:03.062 | 496 | `$k=3` from 2030 | 498: 2111 |
| 23:53:09.361 | 521 | `$k=3` from 2111 | 523: 2111 |
| 23:54:15.007 | 607 | `$k=4` from 2111 | 609: 2120 / A00S, field 17 = 3599 |
| 23:55:37.042 | 655 | `$k=1` from 2120, field 17 = 3518 | 657: 101 / EMSR, field 17 = 0 |

Screenshots show HA's device-derived 0:59:44 countdown alongside MySpeidel's
0 h 59 min display, followed by the main menu in both. All listed records
have flags ph and HTTP 200. The screenshot's unconfirmed message during delay
selection is expected: the hidden selected value is not acknowledged in 2111;
the later 3599-second countdown confirms the combined one-hour selection.
The disabled Select button during countdown is intentional and remains untested.

Snapshot: `captures/2026-11-17-start-delay/diagnostics-ha-validation.jsonl`.
The file spans two sessions; sequence resets must not be mistaken for missing
records. This validates the HA Up/Up/Select/Abort path, not HA Down, manual
editor actions, countdown expiry or Select during countdown.

Additional observation from the same snapshot: cloud `$k=1` in state 2030 at
23:45:50.160 (record 21 of the new session) returns to state 101 at 23:45:52.144
(record 23). This is evidence for initial water-prompt Abort, previously absent
from the captured paths; it is not yet enabled by the published beta.

## Select during countdown: immediate program start, November 18

User repeated HA Up/Up/Select and then pressed Select in MySpeidel while the
countdown was running. At 00:02:01.068 CET, record 1077 of the post-restart
session contains cloud `$k=4` in 2120 / A00S / 000 / ph, field 17 = 3531.
At 00:02:02.219, record 1079 reports 2300 / A000 / 000 / Ph, field 17 = 0,
field 7 = 1. Screenshot shows pump purging. This skips the remaining delay
and starts the program immediately; it is not cancellation back to the menu.
The HA implementation of this newly observed action still needs hardware testing.
Automatic countdown expiry remains untested. Capture saved locally as
`captures/2026-11-17-start-delay/diagnostics-countdown-start-now.jsonl`.
