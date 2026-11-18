# Home Assistant App Store beta channel

Add this exact repository URL in Settings -> Apps -> Install app -> menu -> Repositories:

```text
https://github.com/DanielP-1337/ha-speidel-braumeister#beta
```

[Add repository to Home Assistant](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2FDanielP-1337%2Fha-speidel-braumeister%23beta)

Install **Braumeister Bridge (Beta)** from **Braumeister Bridge — Beta**.
This channel initially contains the tested Bridge 0.5.1-beta.7 runtime from
integration release 3.2.1-beta.9. The channel now includes Bridge 0.5.1-beta.8
from tested integration release 3.2.1-beta.10 (verified resume contexts).
The current update is Bridge 0.5.1-beta.10 from tested release 3.2.1-beta.12,
adding verified hop, Whirlpool and Cheers acknowledgments.
Only the App Store name and links differ from the corresponding release.
The Supervisor builds the AMD64/ARM64 app using the supplied build.yaml;
updates are subsequently offered in the app's Info page when this channel
publishes a higher version. HACS continues to manage the integration,
Menu Companion and Display Card separately.

## One-time migration from the local app

Do this while the Braumeister is idle. Copy the old app's Options YAML.
Install the repository app without starting it, then paste and save those
options. Preserve ports, cloud forwarding, diagnostics and control permissions.
Stop the local app and disable its Start on boot and Watchdog. Only then start
the repository app and enable its Start on boot. Never run both apps together:
they share host ports. Verify fresh device telemetry and cloud forwarding.

Keep the local app installed but stopped as a rollback. Its private /data
directory remains intact; the repository app has a separate private directory.
Historical diagnostics exported to /share remain accessible. The recipe cache
is rebuilt from device messages; device recipes are not overwritten by migration.
Neither old private history nor upload-job history is claimed to be migrated.

Existing integration and Companion endpoints remain unchanged because host
networking and the configured ports are preserved. Automatic updates stay off
by default: choose Update while idle, not during a brew. A Core restart is not
normally required for a Bridge-only update.

Rollback: stop the repository app, disable its autostart, then start the old
local app and restore its previous autostart setting. Never start both.

## Publishing future beta updates

Keep the URL and `beta` branch stable: changing the repository URL changes the
Supervisor repository/app ID. Do not point users at development branches.
After a new coordinated prerelease passes CI, merge its release tag into this
branch, preserve the Beta repository metadata and app display name, and push.
The app's version in config.yaml must increase for HA to offer an update.
Do not publish untested development commits directly to this channel.
Include advancing this branch in every future Bridge beta release checklist.

[Home Assistant repository documentation](https://contributors.home-assistant.io/apps/guides/repository/)
