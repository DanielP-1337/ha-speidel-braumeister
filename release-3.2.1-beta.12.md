# Integration 3.2.1-beta.12 / Bridge 0.5.1-beta.10

This coordinated beta adds the three recorded end-of-brew Select transitions:

| Action | Before | Confirmed result |
| --- | --- | --- |
| Hop acknowledgment | 3080 / qH / 010 | 3070 / qH / 000 |
| Whirlpool confirmation | 3510 / ph / 000 | 3610 / ph / 000 |
| Cheers confirmation | 3610 / ph / 000 | 101 / ph / 000 |

Each action sends key 4 once and waits for the matching device state, actuator
flags and indicator. Existing control permission, fresh-state, pending-command
and cloud-command arbitration remain unchanged. No unverified stop action or
generic confirmation is enabled. The integration runtime is otherwise unchanged;
its version advances with this coordinated Bridge release.

Use Menu Companion 0.1.0-beta.18 and Display Card 0.7.0-beta.28. The Bridge update
is delivered on the existing `#beta` HA App Store channel. Update only while idle.
The source transitions are hardware-observed; the new HA path awaits user testing.
