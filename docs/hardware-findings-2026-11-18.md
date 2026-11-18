# Hardware observations: resume, progress, and audio

User-operated Braumeister 20L Plus, firmware 1.1.27, November 18, 2026.
The new App Store Bridge recorded these transitions. No agent sent brewing commands.

| Action | Before (state / actuators / indicator) | First confirmed result |
| --- | --- | --- |
| MySpeidel Select during purge pause | 2310 / ph / 120 | 2310 / ph / 000 |
| MySpeidel Select during first-rest pause | 2810 / ph / 120 | 2810 / PH / 000 |

The purge case was recorded at sequences 1409 → 1411; alternating purge states
2300/2310 followed, then heating state 2410 at sequence 1457. The first-rest case
was recorded at sequences 2088 → 2090. In both cases field 13 changed from A00F
to A000 and Select was key 4. These sequences belong to the post-migration
recording; private raw logs are retained locally and are not published.

Resume is now allowed only for evidenced paused states 2300, 2310, and 2810,
with actuators ph and indicator 120. Existing administrator, fresh-state,
program-control, remote-heating, and browser-confirmation gates remain.
Resume in heating state 2410, pump break 2820, and other stages remains unverified.
Up/Down in the malt-added prompt still needs a physical-key test.

The user confirmed sound playback on notebook, phone, and tablet. The old card
played once; the device and MySpeidel repeated until acknowledgment. The new
card repeats at six-second intervals while the reported alarm/pause persists,
with an optional one-shot mode and local sound mute (not a process command).

MySpeidel's yellow header progress is visible during heating. The existing
integration decodes field 12 against a full scale of 318 into percentage progress.
The card now uses that progress entity for its existing black header divider.
It does not estimate progress from temperature or elapsed time.
