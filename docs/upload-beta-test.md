# Generic upload beta: installation and test

Pair integration **3.2.1-beta.5** with Bridge **0.5.1-beta.3**.
The existing Companion and Display Card can remain installed. This beta adds
developer/automation actions, not a new upload button in the display card.

1. Update the existing local Bridge app: extract the release's Bridge ZIP into
   the addons share, replacing the contents of `braumeister_bridge` (not nesting
   a second folder). Rebuild/update the same app and check version 0.5.1-beta.3.
   Keep the current options, DNS routing and persistent data. HACS does not update
   the Bridge app. Keep your previous app source/backup for rollback.
2. In HACS, use the existing `DanielP-1337/ha-speidel-braumeister` repository,
   enable prereleases and download 3.2.1-beta.5. Restart Home Assistant.
3. Keep the existing integration entry. For local operation retain Local Bridge
   only and `forward_to_cloud: false`. Enable `recipe_write_enabled` in the Bridge
   for upload testing. Remote heating permissions are not needed for uploads.

## First test: read only

In Developer Tools → Actions, execute:

```yaml
action: speidel_braumeister.recipe_upload_readiness
data: {}
```

With multiple devices specify `config_entry_id`. With the BM off or disconnected,
readiness must become false after the freshness window. With the BM in its main
menu, pump/heater off, no pending command and uploads enabled, readiness should
be true. `connected` means a fresh device status, not an electrical power sensor.

## Upload test

Review and save the current Device Recipes sensor's `recipes` attribute first.
Prepare the **complete desired list**, not just a single new recipe: upload
replaces all device slots. Keep the BM in its main menu with pump/heater off.

Call `speidel_braumeister.start_recipe_upload` with that list in `recipes`, note
the returned `job_id`, then call `speidel_braumeister.recipe_upload_status` with
that ID every few seconds. `confirmed` means the device acknowledged the count;
`content_verification: matched` additionally means a fresh returned list matched.
`not_available` is not an integrity check. Inspect the recipes on the BM itself.

An interrupted upload may leave only part of the list. Never automatically
resubmit after a timeout: query the known job first. Job history is in-memory and
is lost at Bridge restart. This beta has not yet been tested on real hardware.

The [generic API contract](recipe-upload-api.md) includes JSON and automation
examples. HBAC 0.3.0 can also use these actions; no HBAC installation is required.

## Rollback

Redownload integration 3.2.1-beta.4 in HACS and restart HA. Restore the previous
Bridge 0.5.1-beta.2 source/backup into the same app and rebuild. Keep the existing
slug, options and data. Software rollback does not restore overwritten recipes;
retain the recipe list separately.
