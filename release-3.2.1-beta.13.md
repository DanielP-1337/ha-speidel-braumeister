# Integration 3.2.1-beta.13 / Bridge 0.5.1-beta.11

Add exact transitions captured on November 18 in the user-operated hardware test:

| Action | Source | Target |
| --- | --- | --- |
| Resume timed rest | 2820/ph/120 | 2820/PH/000 |
| Confirm lid removed | 3010/qH/0D0 | 3010/qH/000 |
| Pause at hop prompt | 3080/qH/010 | 3080/ph/120 |
| Resume hop prompt | 3080/ph/120 | 3080/qH/010 |

Existing 0DT to 00T lid acknowledgment remains supported. State/flag/indicator
checks, heating permissions and queued-command rechecks remain enforced.
Use Companion 0.1.0-beta.19 and Display Card 0.7.0-beta.31.
HA hardware validation is pending; source transitions were observed via MySpeidel.
Heating-to-boil controls and final abort from the hop pause are not added.
