# Mash-in controls and notifications — November 18, 2026

Braumeister 20L Plus, firmware 1.1.27. Diagnostic session
`072049aaab744ffb9ade707ae97091c5`. Raw captures remain local; no credentials,
recipe payloads or original MySpeidel sound are published.

| Command record | Origin / key | Before: state, flags, labels, indicator | Next status record and result |
|---|---|---|---|
| 320 | HA/local_control / 4 | 2120, ph, A00S, 000; remaining 3509 s | 322: 2300, Ph, A000, 000; remaining 0 |
| 389 | MySpeidel/cloud / 1 | 2310, ph, A000, 000 | 391: 2310, ph, A00F, 120 (paused) |
| 431 | MySpeidel/cloud / 1 | 2310, ph, A00F, 120 | 433: 101, ph, EMSR, 000 |
| 1253 | HA/local_control / 4 | 2111, ph, ADUS, 000; Up/Up/Down/Down previously | 1255: 2300, Ph, A000, 000 (zero-delay start) |
| 1289 | HA/local_control / 1 | 2300, Ph, A000, 000 | 1291: 2300, ph, A00F, 120 |
| 1348 | HA/local_control / 1 | 2300, ph, A00F, 120 | 1350: 101, ph, EMSR, 000 |
| 2675 | MySpeidel/cloud / 4 | 2510, Pi, A00S, 010 | 2677: 2610, ph, A00S, 000: Add malt |
| 2800 | MySpeidel/cloud / 4 | 2610, ph, A00S, 000 | 2802: 2705, ph, ADUS, 000: Malt added? |
| 2908 | MySpeidel/cloud / 4 | 2705, ph, ADUS, 000 | 2910: 2810, PH, A000, 000: first mash rest |
| 3118 | MySpeidel/cloud / 1 | 2810, PH, A000, 000 | 3120: 2810, ph, A00F, 120: paused |
| 3210 | MySpeidel/cloud / 1 | 2810, ph, A00F, 120 | 3212: 101, ph, EMSR, 000: final abort |

The initial direct Select from 2030 and the newly enabled HA routes still need
hardware validation. The exact cloud mash transitions above are confirmed,
not yet their new HA implementation. Cancel from other newly enabled mash
prompts and 2820 also needs hardware validation. Resume from a paused first
rest has not yet been captured.

Up/Down at Malt added? (2705) had no recognizable effect through MySpeidel.
User requested a TODO for a physical-device test. They remain disabled until
their meaning and observable result are established.

Mash temperature reached is a normal process notification, not a danger alarm.
The Hue blueprint distinguishes normal notifications (default green) from
pause/unclassified alarm (default red), with both colors configurable in HA.
