# Diagnostics mapping beta

Release **3.2.1-beta.6** packages integration version 3.2.1-beta.6 and Bridge
**0.5.1-beta.4**. Integration behavior is unchanged; this release adds Bridge
diagnostics. Existing integration beta.5 remains compatible.

HACS updates only the integration. For the existing local Bridge app, extract
the release asset `Braumeister-Bridge-0.5.1-beta.4.zip` into the HA `addons` share,
replacing the `braumeister_bridge` source folder. Preserve options and app data.
Refresh the app store and update/rebuild the existing local app when the
Braumeister is idle. Verify Bridge version 0.5.1-beta.4 before testing.

In HACS select prerelease 3.2.1-beta.6 for the existing custom repository
`DanielP-1337/ha-speidel-braumeister` if you also want its matching integration
version. An integration-only update does not install the new recorder or mount.

Enable `diagnostics_enabled` and `diagnostics_export_to_share` in the Bridge
configuration, save and restart the Bridge. No device control options need to
be changed. New exchanges create
`\\homeassistant.local\share\braumeister-bridge-diagnostics.jsonl`.
Copy this and the `.previous.jsonl` file if present after testing.

See the [capture fields, retention and mapping checklist](../braumeister_bridge/DOCS.md#export-diagnostics-to-the-ha-share-bridge-051-beta4).
This beta collects evidence; it does not implement unverified editor actions.

Rollback: reinstall the previous Bridge source (0.5.1-beta.3); remove the new
`diagnostics_export_to_share` option if the older schema requests it. Exported
files remain in `/share`. No live hardware validation of this recorder is claimed.
