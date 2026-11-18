# Integration 3.2.1-beta.16 / Bridge 0.5.1-beta.14

Enable three exact hardware-observed transitions:

- Normal remove-lid Cancel: `3010/qH/0D0` -> `3010/ph/120`, key 1 (recorder 2843 -> 2845).
- Final Cancel from the heating-stage pause: `3010/ph/120` -> `101/ph/000`, key 1 (2856 -> 2858). This is a separate action, not a one-click abort at the lid prompt.
- Hot-start mash acknowledgment: `2510/qi/010` -> `2610/ph/000`, key 4 (3212 -> 3214). The previous implementation accepted only Pi at this prompt.

Observed November 18, 2026 on a user-operated Braumeister 20 L Plus, firmware 1.1.27, through MySpeidel and subsequent device telemetry. Fresh-state checks, arbitration, opt-ins, and exact target confirmation remain in place. Editor-associated lid cancellation (0DT), boil editors, and final abort from hop/completion pauses remain outside this change.

Use Card 0.7.0-beta.36 and Companion 0.1.0-beta.23. Integration code is unchanged; its version advances to package the coordinated Bridge release. New HA paths need the next hardware validation; no development-agent device commands were sent.
