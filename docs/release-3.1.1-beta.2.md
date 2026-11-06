# Speidel Braumeister Integration 3.1.1-beta.2 — efficient heartbeat state updates

Includes the recorder/history correction reviewed in upstream PR #23
(`2a5e55b`). This is an integration-only prerelease for the existing HACS fork.

- Timer and coordinator callbacks only publish when the warning, risk or other
  meaningful activity metadata changes. Unchanged healthy operation and an
  unchanged outage no longer cause periodic HA state writes.
- Removes `age_seconds` from entity attributes. Timestamp-only advancement is
  ignored for publication. `last_device_timestamp` is a snapshot refreshed on
  meaningful publication, not a continuously updated age indicator.
- Keeps the 120-second expiry, five-second passive check, retained heater
  permission (including `i`), and warning/recovery behavior.
- Preserves beta 1's entity IDs, configuration and display compatibility fields.
- Adds full-day publication-count regressions and an Unreleased changelog entry.

## Install through HACS

Back up the current integration first. In the existing
**DanielP-1337/ha-speidel-braumeister** HACS repository, enable prereleases and
select **3.1.1-beta.2**. Restart Home Assistant after installation, then reload
the dashboard. Do not remove/re-add the device. The version shown for the
integration should be `3.1.1-beta.2`.

Keep the existing `entities.connection_warning` mapping. **Display Card,
Companion and Bridge need no update.** No options, DNS settings or command
allowlists need changing. No automatic control commands or extra cloud/device
requests are introduced. Installing this beta does not remove existing history.

## Validation and remaining limits

The synthetic publication-count test covers 24 hours of advancing device polls
every 30 seconds and passive checks every five seconds: only the initial healthy
transition is published. An unchanged subsequent outage adds one warning
transition, and recovery adds one state change. This tests sensor publication
behavior with HA API stubs; it is not an on-device recorder database measurement.

The complete beta branch passed **244 tests and 261 subtests**, full-repository
Ruff and `git diff --check`.

User-reported beta 1 hardware results confirmed the yellow warning after idle
power-off and the red warning after power-off with the heater last known active.
The beta 2 recorder-write correction still needs verification in real HA.
Reconnection, network-only failure with power maintained, failure during an
automatic brew/regulation pause and isolated-network operation remain pending.
Alternate account/system/browser locales and units are not hardware validated.

Restart/reload resets heartbeat evidence and retained activity. HA downtime or
a browser disconnected from HA cannot be monitored by this mechanism. Retained
activity is last known; current physical state after connection loss is unknown.

For rollback, redownload the previously installed integration version in HACS
and restart HA. Beta 1 uses the same diagnostic entity and card mapping but lacks
this write-suppression correction. No other component needs rollback. Restore
behavior has not been hardware tested.
