# Heating-to-boil pause with qH

User-operated Braumeister 20 L Plus, firmware 1.1.27, November 18, 2026.
Times are Europe/Berlin (UTC+01:00). The HA error identifies
`request_program_pause`, state 3010, actuators qH, indicator 000.

The current recorder export confirms:

| Time | Sequence | Event |
| --- | --- | --- |
| 19:03:00.433 | 1941 | Cloud key 1 from `3010/A00S/qH/000` |
| 19:03:02.401 | 1943 | Pause: `3010/A00F/ph/120` |
| 19:03:09.023 | 1961 | Cloud key 1 from that pause |
| 19:03:11.088 | 1963 | Main menu: `101/EMSR/ph/000` |

This is normal heating-to-boil (indicator 000), not an active remove-lid prompt
(0D0). The earlier beta accepted PH/000 and qH/0D0, but not qH/000. The Bridge
and Companion source mapping now accept this additional exact pause context.
The final-abort transition was already supported and is reconfirmed here.

No resume transition from this qH-origin pause was captured; do not infer a new
resume target. Editor contexts and other actuator combinations are unchanged.
Synthetic exchange and adapter tests cover qH/000 acceptance and rejection of
qH/00T and qi/000. New HA-path hardware validation and the next release remain
pending. No raw captures, device identifiers, or upstream PR are published.
