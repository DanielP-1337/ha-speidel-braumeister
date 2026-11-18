# Integration 3.2.1-beta.14 / Bridge 0.5.1-beta.12

New user-operated MySpeidel evidence from November 18:
- Sequence 9711 key 1: 3450/ph/010 -> 9713 3450/ph/120.
- Sequence 9794 key 4: 3450/ph/120 -> 9796 3450/ph/010.
- Sequence 9859 key 4: 3450/ph/010 -> 9861 3510/ph/000.

Implement these exact pause, resume and Brewing complete acknowledgment rules.
No generic final-abort or heating/editor permissions are added. Includes beta.13
fixes for timed-rest resume, normal lid acknowledgment and hop pause/resume.
Use Companion beta.20 and Card beta.32. The user also confirmed the existing
Whirlpool and Cheers actions through HA on real hardware; the new completion
actions still require HA hardware validation.
