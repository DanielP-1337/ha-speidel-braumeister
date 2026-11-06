# Passive device connection watchdog (3.1.1-beta.2)

Fork prerelease based on upstream integration v3.1.0, commit `8f61ab4`. This change does not
change Bridge code or command handling. No additional cloud/device requests,
automatic shutdowns, notifications, or control actions are generated.

The new diagnostic problem binary sensor **Check device connection** observes
the integration's existing bridge/XHR results. Two successive, advancing device
timestamps establish a heartbeat. A successful HTTP response or repeatedly
cached status does not count as fresh device evidence. The sensor becomes on
after 120 seconds without advancing evidence; a local five-second timer keeps
this working when the coordinator's requests fail or hang. Actual detection is
within about five seconds of the threshold while HA's event loop is running.
Network recovery is recognized on the next normal integration update, not by an
extra probe. This is device-telemetry freshness, not proof of every LAN route.

Beta 2 only publishes HA state when warning, risk or other meaningful metadata
changes. This applies to timer and coordinator callbacks. `age_seconds` is no
longer an entity attribute, and timestamp-only advancement does not publish.
`last_device_timestamp` is a snapshot refreshed on meaningful publication,
including expiry and recovery; it is not a continuously updated age indicator.
The internal monotonic expiry still uses every valid advancing device sample.

Startup is unknown until advancement is observed. No evidence for 120 seconds
also raises a warning, with `evidence: unconfirmed`. Missing timestamps and
MQTT/API data without verified device timestamps cannot prove recovery. Source
changes and backwards clock jumps require a new advancing pair. Host monotonic
time controls expiry; changing HA's wall clock does not extend the deadline.

Attributes retain last known brewing state, heater permission, heater output,
pump output and state code. Unknown/incomplete fields do not overwrite known
activity. Heater flag `H` means output on; `i` means permission enabled while
regulating, and also counts as a potential hazard; `h` means permission off.
`activity_at_risk` is true during an outage when brewing, heater permission or
heater output was last known active. Brewing follows upstream `process_status`,
which also classifies some preparation screens as running; this is conservative
and does not prove a brew was actually heating. These are **last known** values,
never assertions of current physical state. Pump-only activity is retained but
does not escalate the red brewing/heating warning.

The sensor remains available when ordinary entities become unavailable because
of coordinator errors. HA state changes can be used by user-defined notification
automations; none are installed automatically. This cannot alert while HA itself
is stopped, its event loop is blocked, or the dashboard is disconnected from HA.
Restart/reload resets evidence and retained activity; no restore-state latch is
implemented. Offline/isolated-network operation has not been hardware tested.

Configure the matching sensor under Display Card `entities.connection_warning`
after both changes have been installed. Use the entity ID shown for your actual
device; no installation-specific ID is assumed. The existing companion requires
no change: it does not provide or consume this diagnostic entity.

The fork beta also retains the previous fork's `current_step` display clock,
raw actuator flags and mash-rest timer attributes, which upstream v3.1.0 omits.
XHR and bridge data both supply these fields. Invalid/malformed flags remain
unknown. This preserves existing companion/card manual controls without changing
the installed Bridge, its command allowlist or the companion services. Existing
entity IDs/options are retained; upstream 3.1.0 enum sensor values are `on`/`off`
and translated by HA, rather than the older fork's literal `Ein`/`Aus` values.
Custom templates comparing those literal strings may need adjustment.

Local regression coverage: frozen payloads, missing/invalid timestamps, startup,
source changes, backwards timestamps, recovery, retained activity, regulation and
pump-pause flags, coordinator failure visibility, timer registration/removal.
The HA lifecycle test uses API stubs, not a real HA runtime. The tester has now
reported yellow-warning behavior after powering off an idle appliance and
red-warning behavior after powering off with the heater last known active.
These are power-loss tests, not network-only outages. Recovery/reconnection,
outage during an automatic brew and an outage during regulation pause remain
pending on hardware. The screenshots do not establish the exact detection delay.
No services were restarted or changed for the local automated tests.
