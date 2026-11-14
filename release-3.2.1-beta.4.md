# Local Bridge discovery and setup validation

Includes the reviewed setup changes from upstream PR #29 on top of the tested local-mode beta.3.

- New local setup offers devices discovered through the local Bridge status API.
- Checks Bridge connectivity and the selected device before saving. Unreachable Bridge, no known devices and unknown IDs show recoverable errors; manual entry is available when discovery has no devices.
- Prevents duplicate entries across long local IDs and combined cloud UUIDs, including case differences.
- Clarifies that local operation requires the configured Braumeister Bridge app.
- Existing local entries still start offline and recover when the Bridge/device returns. Five-second polling and immediate refresh after supported control actions are retained.

## Install and test

In HACS, enable prereleases for DanielP-1337/ha-speidel-braumeister, download **3.2.1-beta.4**, then restart Home Assistant. Keep your existing integration entry and entity mappings.

Only the integration needs an update. Continue using Bridge **0.5.1-beta.2**, Companion **0.1.0-beta.12** and Display Card **0.7.0-beta.22**. Keep **Local Bridge only** enabled and `forward_to_cloud: false` in the Bridge app.

Test normal operation first. To check duplicate handling, start adding a local integration and select the already configured brewer: setup should report that it is already configured. Do not delete the working entry. Discovery requires a running Bridge with a known device; this requirement applies only to new setup, not startup of an existing entry.

For a complete offline test, block WAN access while preserving LAN/DNS access, restart HA/Bridge and check status recovery and supported controls. Full WAN-blocked hardware validation remains pending.
