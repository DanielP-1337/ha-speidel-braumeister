# Manual temperature editor: hardware observation, 2026-11-17

Evidence: eight supplied MySpeidel screenshots and two diagnostic JSONL snapshots
of the same session. The first snapshot contains 395 records; the second extends
it with an identical first 395 records. Do not count the overlap as separate trials.
Times below are Bridge Unix timestamps converted to Europe/Berlin (UTC+01:00),
not the device's minute-resolution display clock.

## Observed actions

| Response time (CET) | Command record | Command | Incoming state | First observed result |
|---|---|---|---|---|
| 22:20:28.185 | 62 | `$k=2` | 101 / EMSR / 000 | Record 64: 4006 / APHT / 000; manual mode, target 38 C |
| 22:21:00.894 | 113 | `$k=4` | 4006 / APHT / 000 | Record 115: 4007 / ADUS / 00T; temperature editor |
| 22:21:23.820 | 158 | `$k=3` | 4007 / ADUS / 00T; target 380 | Record 160: target 390 (38 -> 39 C) |
| 22:21:41.436 | 197 | `$k=2` | 4007 / ADUS / 00T; target 390 | Record 199: target 380 (39 -> 38 C) |
| 22:22:04.022 | 240 | `$k=4` | 4007 / ADUS / 00T | Record 242: 4006 / APHT / 000; target 380 |
| 22:22:28.562 | 285 | `$k=4` | 4006 / APHT / 000 | Record 287: 4007 / ADUS / 00T; target 380 |
| 22:22:51.912 | 330 | `$k=1` | 4007 / ADUS / 00T | Record 332: 101 / EMSR / 00T; target -1000 |

All seven key responses have source `cloud` and HTTP 200. All observed status
records show actuator flags `ph`; no active pump/heater flag is observed.
The result is the next available status record, not necessarily the next
exchange: some exchanges do not carry status fields.

## Conclusions and limits

- In the manual temperature editor, keys 1/2/3/4 correspond to
  Abort/Down/Up/Select. Up and Down change the displayed target by 1 C in this trial.
- Select returns to manual mode. Abort exits directly to the main menu;
  no intermediate manual-mode status or second Abort command was captured.
- Field 13 matches the visible four labels: EMSR (main), APHT (manual),
  ADUS (editor).
- Field 15 `00T` persists after Abort in the main menu through the final record.
  It is NOT sufficient on its own to identify an active editor. State and
  field 13 must be considered together with field 15.
- The initial Abort test did not change the target before cancelling. The
  follow-up below confirms that the changed value is discarded in this trial.
- A single sequence gap occurs after record 395 (record 396 is absent), after
  the test actions. No sequence gaps occur across the seven action/result pairs.
- Screenshots support the UI interpretation; their device clock is not exactly
  synchronized with the Bridge timestamps and must not be used for second-level timing.
- Rest/boil editors, held buttons, limits, Fahrenheit and persistence across
  power cycles are untested. Do not generalize these commands to other states.

No device actions or code changes were made during this analysis.

## Follow-up: Abort after changing the target

The user reported that Abort discards the edited value. A read-only check of
the live `/share/braumeister-bridge-diagnostics.jsonl` confirms this sequence
in the same session (times CET, 2026-11-17):

| Command time | Command record | Command | Result record and observation |
|---|---|---|---|
| 22:28:36.739 | 648 | `$k=2` | 650: manual mode 4006, target 380 (38 C) |
| 22:28:43.920 | 672 | `$k=4` | 674: editor 4007 / ADUS / 00T, target 380 |
| 22:28:50.318 | 695 | `$k=3` | 697: editor target 390 (39 C) |
| 22:28:55.907 | 717 | `$k=1` | 719: main menu 101 / EMSR / 00T, target -1000 |
| 22:29:07.264 | 749 | `$k=2` | 751: manual mode 4006 / APHT / 000, target 380 (38 C) |

Reopening manual mode restores the original 38 C rather than the edited 39 C.
Thus Abort exits to the main menu and the unconfirmed edit is discarded for
this tested path. The main-menu -1000 sentinel alone would not prove rollback;
the decisive evidence is record 751 after reopening. All five command records
have source `cloud`; all listed result records show `ph`.
This does not establish behavior in rest/boil editors or across a power cycle.
