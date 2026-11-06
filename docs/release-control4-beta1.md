# Braumeister Bridge 0.3.2-control.4-beta.1

Experimental local-app update for the existing `local_braumeister_bridge`.
This is **not** a HACS integration update. Keep HA integration 3.1.1-beta.2 (or
your current integration) unchanged. Matching HACS components are Companion
0.1.0-beta.6 and Display Card 0.7.0-beta.8.

## Enabled scope

- Recipe Select: 2015/ph/000 -> 2030/ph/000, at the water prompt only.
- First Cancel: pause purging at 2300 or heating at 2410; confirmation requires
  the same screen code, ph and indicator 120.
- Second Cancel from those pause dialogs: final abort to 101/ph/000.
- Resume: **purging at 2300 only**, to 2300/Ph/000. Requires both new
  `program_control_enabled: true` and existing `allow_remote_heating: true`.
  The program option defaults to false; existing actuator permissions remain.

All actions still require `control_enabled`. Pause/final abort do not require
enabling resume. Water confirmation, water-prompt Cancel, delayed-start keys,
state 2310 and heating-stage resume remain unsupported. Do not expect this beta
to start a full brew from the dashboard.

## Existing local-app installation path

Only update when no brew is active and pump/heater are off. Preserve the current
app backup, source, options and persistent data before changing files. Confirm
the installed/source versions first:

```sh
ha apps info local_braumeister_bridge |
  grep -E '^(version|version_latest|update_available|state):'
grep '^version:' /addons/braumeister_bridge/config.yaml
```

Extract the supplied ZIP, then copy its **braumeister_bridge contents** into the
already confirmed Samba folder `\\homeassistant.local\local_apps\braumeister_bridge`
(HA source path `/addons/braumeister_bridge`). Do not nest another app folder,
delete/reinstall the app, replace private `/data/options.json`, or copy over `/data`.
Review the existing options; especially preserve the working `dns_port: 0`,
cloud DNS and forwarding settings. New source defaults are not a reason to reset
installed options.

Refresh the local app store if needed. Once the update is detected:

```sh
ha apps update local_braumeister_bridge
ha apps info local_braumeister_bridge |
  grep -E '^(version|version_latest|update_available|state):'
curl -fsS --max-time 5 http://127.0.0.1:8642/api/health
```

This rebuilds/restarts only the Bridge through Supervisor. Keep existing options
and persistent data. For purge resume, explicitly set the two Bridge options
above; do not enable them merely for menu selection or cancellation tests.

Install Companion 0.1.0-beta.6 and Card 0.7.0-beta.8 through their existing HACS
repositories, selecting prereleases. Restart HA once for the Companion update,
then reload the browser. Preserve `braumeister_menu.device_id`, card entities,
`menu_control`, existing actuator opt-ins and `connection_warning` mapping.
Card `program_control: true` opts into purge resume; it does not bypass the two
Bridge permissions. Final abort and resume have separate UI confirmations.

## Validation and boundaries

- 220 Bridge tests and 261 subtests, full Ruff and diff checks passed.
- 17 Companion tests passed; seven Card test scripts passed.
- Actual Add-on Dockerfile built for linux/arm64 with
  `BUILD_FROM=ghcr.io/home-assistant/aarch64-base:3.24`.
- ARM64 runtime tested under emulation on a linux/amd64 Docker Desktop engine,
  using an internal-only network, synthetic device requests and a local mock
  cloud. No productive data or Docker socket was mounted. Tests covered startup,
  exact transitions/indicators, no duplicate keys, cloud priority, gzip/binary
  forwarding, local fallback, recipe persistence, and default-denied resume.
- The Dockerfile's required `BUILD_FROM` argument has no default, so Docker emits
  `InvalidDefaultArgInFrom`; the build explicitly supplies the correct value.

This is not a Raspberry Pi hardware test. User-operated MySpeidel observations
provided the bounded transition evidence; the new **local** command path still
needs hardware validation. Additional locales/units and network-only outages
remain untested. No HA/device actions were performed by the automated tests.

## Rollback

Preserve the exact pre-update source/options/app backup. Restore that previous
source into the same confirmed folder and rebuild the existing app through
Supervisor, or restore **only this app** from its backup. If a lower source
version is not offered as an update, use the app's Rebuild action rather than
deleting it. Keep the same slug and private data. Do not restore other HA
components or a full HA backup for this update.

For Companion/Card rollback, redownload their previous versions through HACS;
restart HA for the Companion and reload the browser for the Card. Remove the
new `program_control` card opt-in if reverting. Restore behavior is untested;
stop and inspect errors if a Bridge-only rollback cannot be performed cleanly.
