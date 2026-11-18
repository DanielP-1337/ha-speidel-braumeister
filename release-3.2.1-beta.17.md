# Integration 3.2.1-beta.17 / Bridge 0.5.1-beta.15

Two narrowly scoped corrections from the November 18 user-operated tests:

- Accept Cancel in normal heating-to-boil context `3010/qH/000`, confirming the paused target `3010/ph/120`. MySpeidel key 1 at 19:03:00 (sequence 1941) reached the pause at 1943; a second Cancel reached the main menu at 1963. The final-abort mapping was already supported.
- When acknowledging rest end from `2910/Pi/010`, accept either observed target `2930/pi/000` or `2930/pH/000`. The pH target was captured at 18:50:48 (1190), following MySpeidel key 4 at 1188. Source PH keeps its previously observed pi target.

Source `2910/qi/010` remains unverified and rejected. No boil editor or other source/target permissions are added. Exact target indicators, fresh status, command arbitration and existing control options remain enforced.

Use Companion 0.1.0-beta.24 and Display Card 0.7.0-beta.37. The integration version packages the updated Bridge; integration runtime code is unchanged. Update the Bridge through the existing App Store beta repository while idle. Restart HA for the Companion and reload the dashboard.

Cloud transitions are hardware-confirmed; the new HA paths await hardware validation. No upstream PR is opened.
