Local-only mode with five-second Bridge polling (hardware test beta).

Required: Integration 3.2.1-beta.3 and Companion 0.1.0-beta.12. Existing Display Card 0.7.0-beta.22 and Bridge 0.5.1-beta.2 can remain installed.

Setup for an existing installation:
1. Update Integration and Companion in HACS with prereleases enabled; restart Home Assistant.
2. In the Speidel Braumeister integration's Configure/Options dialog, enable Local Bridge only (Nur lokale Bridge). Keep the existing entry and entity mappings. The cloud polling interval shown alongside this option is ignored in local mode: Bridge polling is fixed at five seconds.
3. In the Bridge app configuration, set forward_to_cloud: false and restart the Bridge. Retain existing DNS, device, control and heating permissions. MySpeidel will no longer receive current device status.
4. New local installations can select Local Bridge only on the initial setup form, leave cloud credentials blank, and enter the device ID reported by the Bridge. No cloud account or login is required.

Local mode creates no cloud clients, performs no cloud login or metadata requests, does not fall back to the cloud, and does not fetch cloud diagnostics. It can start while the device/Bridge is unavailable, then recover on a later local poll. Messages older than ten seconds are treated as offline. The device's own reporting cadence and HTTP request duration still contribute to end-to-end latency.

The Companion accepts fresh acknowledged local responses for the already-supported control actions, preserving admin, status, flag, age and Bridge permission checks. A confirmed action emits a local event requesting an extra integration refresh. Existing unverified brewing controls remain unavailable.

For the hardware test, verify temperature, phase, timers, pump/heater indications and supported menu actions. Then block internet access while preserving LAN/DNS access and verify HA/Bridge restart, device-off detection and recovery. Internet-disconnected hardware validation is pending; automated tests cannot establish it.

The existing cloud-capable mode remains available. A cloud-created entry can be switched back using its retained credentials. A new credential-free entry must be configured with a cloud account separately to use cloud mode.
