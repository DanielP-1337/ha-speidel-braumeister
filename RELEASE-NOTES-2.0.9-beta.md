# 2.0.9-beta - RTC monitoring hardware test

Backports the RTC diagnostics from upstream PR #15 onto 2.0.8-beta.

- Adds signed RTC offset in minutes and a sustained Check RTC problem sensor.
- Rejects stale samples and resets evidence after clock/source discontinuities.
- Preserves adaptive polling, backoff, local bridge behavior and display attributes.
- Includes tzdata for Windows tests. Bridge remains 0.1.4; display card is unchanged.
- No clock writes, device commands or automatic notifications are added.

Install through HACS and restart Home Assistant. Configure the HA timezone to
match the device, then follow docs/rtc-monitor.md. Hardware validation is pending.
A +3 minute offset should not warn; a +8 minute offset should warn after at least
three minutes of fresh abnormal observations. Restore the device clock afterward.

Validation: 184 Python tests and 297 subtests passed, including the beta XHR
parser-to-coordinator path; existing dashboard tests passed.
