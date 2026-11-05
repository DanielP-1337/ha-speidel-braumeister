# Speidel Braumeister Integration 3.1.1-beta.1 — device connection watchdog

Fork prerelease based on upstream v3.1.0 (`8f61ab4`). This is an integration
release, not a Bridge update. Keep the existing Bridge and Companion installed.

- Adds the diagnostic **Check device connection** problem binary sensor.
- Warns after 120 seconds without advancing bridge/XHR device timestamps,
  independently of failed or stalled integration polls, with five-second checks.
- Retains last-known brewing, heater-permission and actuator activity; heater
  regulation flag `i` counts as enabled permission, not confirmed active output.
- Preserves the previous fork's display clock, actuator flags and mash-rest timer
  attributes for Display Card and Companion compatibility with the upstream base.
- No extra cloud requests, device probes, shutdown commands or notifications.

## Install and connect the card

In the existing **DanielP-1337/ha-speidel-braumeister** HACS repository, enable
prereleases and select **3.1.1-beta.1**. Create a backup before updating. Restart
Home Assistant after installing the integration. Do not remove/re-add the device.
The manifest version should then be `3.1.1-beta.1`.

Open the integration's existing device and find **Check device connection**
(German: **Geräteverbindung prüfen**). Copy that entity's actual ID into Display
Card **v0.7.0-beta.7** YAML:

```yaml
entities:
  # Preserve all existing mappings; add this key to the same entities section.
  connection_warning: binary_sensor.YOUR_ACTUAL_CONNECTION_WARNING_ENTITY
```

Do not create a second `entities:` block. Startup is unknown until two advancing
device samples arrive. The Companion needs no update. The Card reloads in the
browser; its update alone does not require an HA restart.

Upstream v3.1.0 uses `on`/`off` enum sensor values with HA translations. Custom
dashboard templates comparing literal `Ein`/`Aus` from the older fork may need
adjustment. This Card supports both representations. Existing IDs/options remain.

## Validation and limits

Local result: **242 tests and 261 subtests passed**, full-repository Ruff and
`git diff --check` passed. HA entity lifecycle is covered using HA API stubs.
The matching Card's six Node test scripts also passed.

Real HA installation, real disconnect/reconnect behavior and isolated-network
operation are **not yet validated for this beta**. Previous live testing used
German, Celsius, Plato, German date/time formatting and Europe/Berlin. Alternate
account units/language, system/browser locales and corresponding RTC behavior
remain untested on hardware. Synthetic Fahrenheit label handling is covered.

The watchdog cannot alert while HA is stopped or the dashboard is disconnected
from HA. Restart/reload resets evidence and retained activity. Cached MQTT/API
data without verified device timestamps cannot establish heartbeat health.
Alerts describe last-known activity, never current physical state. No automatic
safety shutdown is provided.

For rollback, reinstall the previously recorded integration version in the
same HACS repository and restart HA; retain the previous backup. Remove the
`connection_warning` mapping if rolling back to a version without that entity.
No rollback of the Bridge, Companion, DNS or other HA components is required.
Restore behavior has not been hardware tested.
