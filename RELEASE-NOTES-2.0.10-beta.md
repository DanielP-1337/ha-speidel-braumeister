# 2.0.10-beta - Restore cloud display clock and metadata

- Supply validated display_clock, P/H flags and rest timer attributes through the
  XHR cloud path, matching the existing bridge display metadata.
- Keep clock display independent of the RTC diagnostic baseline and warning.
- Preserve RTC monitoring, polling, backoff and device command behavior.
- No display-card update or bridge update is required.

Install through HACS and restart Home Assistant. The current-step sensor should
expose display_clock and the card should show the device clock again when fresh
XHR data is available. Invalid or offline clock data remains blank.

Validation: 187 Python tests and 297 subtests plus existing dashboard tests.
Hardware confirmation is pending.
