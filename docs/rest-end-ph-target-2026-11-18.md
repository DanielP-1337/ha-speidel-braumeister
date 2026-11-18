# Rest-end acknowledgment: pH target variant

Observed on a user-operated Braumeister 20 L Plus, firmware 1.1.27,
November 18, 2026. Times are Europe/Berlin (UTC+01:00).

| Time | Recorder sequence | Observation |
| --- | --- | --- |
| 18:49:10.874 | 1114 | Rest-end prompt: `2910/A00S/qi/010` |
| 18:50:11.650 | 1162 | Same prompt changes to `2910/A00S/Pi/010` |
| 18:50:44.890 | 1188 | MySpeidel key 4, source `cloud`, in `2910/A00S/Pi/010` |
| 18:50:48.191 | 1190 | Remove malt pipe: `2930/A00S/pH/000` |

The Bridge acknowledgment mapping now accepts both observed target actuator
values `pi` and `pH` for Select from `2910/Pi/010`. The existing `PH` source
keeps its previously observed `pi` target. Target screen 2930 and indicator
000 remain mandatory; other actuator combinations are not inferred.

This changes telemetry confirmation, not the emitted command (key 4).
The next action, confirming malt-pipe removal from `2930/pH/000`, was already
supported. Neither Card nor Companion needs a new action for this target variant.

The earlier HA rejection occurred while the source was `qi`. There was no
Select command under qi in this recording. Source `2910/qi/010` remains
unverified and rejected. Do not conflate a new target variant with permission
for a different source state.

Validation includes a simulated end-to-end exchange confirming the pH target
only with the correct indicator, and a negative test retaining qi rejection.
This source change awaits the next beta release and HA hardware validation.
No device commands, raw diagnostics, or upstream PR are part of this change.
