# Hardware mapping and countdown beta

Coordinated releases for testing on the Braumeister 20L Plus / firmware 1.1.27:

| Component | Version |
|---|---|
| Display Card | **v0.7.0-beta.23** |
| Menu Companion | **v0.1.0-beta.13** |
| Speidel integration | **3.2.1-beta.7** |
| Bridge app | **0.5.1-beta.5** |

## What changes

- The card displays the **actual device countdown as H:MM:SS**, using status
  field 17 only in the verified countdown state 2120. It refreshes with HA
  telemetry and is hidden offline; missing values show a dash, never a guessed zero.
- The old unverified-delay warning is replaced with the countdown or, during
  selection, a description of the observed +/-30-minute controls. Eight bundled
  languages include the new text, with en-US fallback.
- Manual temperature editor: open, Up/Down, Select, Abort. Up/Down are limited
  to whole Celsius values in 0..100 C and require both actuators off. Abort
  returns to the main menu and discards the unconfirmed edit in the tested path.
- Delayed start: Up from the water prompt (2030), Up/Down in selection (2111),
  Select from 2111, and Abort from selection or active countdown (2120).
- Each Bridge action requires fresh state, correct button labels/editor flags,
  matching actuator state and no pending action/upload. Context is checked again
  before sending. Commands are sent once and are not automatically retried.

## Installation

1. When the device is idle, extract **Braumeister-Bridge-0.5.1-beta.5.zip** into
   `\\homeassistant.local\local_apps`, replacing the existing `braumeister_bridge`
   folder. (`addons` is the older alias.) Refresh the HA app store and update/rebuild
   the same local Bridge app. Preserve its options and persistent data.
2. In HACS, enable prereleases and download the integration, Companion and card
   versions above from their existing DanielP-1337 custom repositories.
3. Restart HA to load the updated Python integrations, then reload the dashboard
   (hard refresh if the old card remains cached). HACS updates do **not** update
   the separate Bridge app.
4. Preserve your current card entity mappings and Companion device ID.

For card navigation, retain `menu_control: true`. Add `program_control: true`
for delay adjustment/confirmation. The Companion requires an HA administrator.

Bridge navigation requires `control_enabled: true`. Confirming a delayed start
also requires **both** `program_control_enabled: true` and
`allow_remote_heating: true`, plus the card's confirmation dialog: the scheduled
program may later energize the heater/pump, and a zero selection may start sooner.
Cancellation does not require remote heating permission. Diagnostic capture is
optional (`diagnostics_enabled` and `diagnostics_export_to_share`).

## Hardware test sequence

With the device ready for the intended operation, first verify manual editor
38 -> 39 -> 38 C and Select; repeat with a changed value and Abort. Then use
the water prompt: Up twice -> Select -> verify approximately 1:00:00 countdown
-> Abort -> main menu. Check the physical device and HA together and save the
diagnostic export. Do not leave a test countdown armed unintentionally.

The selected delay is **not available in the captured fields while in 2111**.
HA does not estimate it by counting button presses. A delay arrow in 2111 can
therefore report `unconfirmed` despite successful delivery; the unchanged screen
cannot prove the hidden value changed. Do not automatically retry it.

Initial Down/Abort in 2030, immediate-start confirmation, Select during countdown,
and rest/boil editor actions remain unavailable in this beta because these exact
paths have not been captured. Countdown expiry has not been hardware-tested.
The observed +30/-30 minutes and manual +/-1 C are not claims about limits,
held buttons, Fahrenheit, other firmware or other Braumeister models.

## Evidence and validation

Hardware evidence comes from user-operated MySpeidel and physical buttons,
screenshots, and sanitized diagnostic exchanges on November 17, 2026.
The new HA action implementations themselves still need the requested hardware test.

- 356 core tests and 280 subtests; 39 HA integration tests.
- 47 Companion tests; all card suites including the new countdown suite.
- Ruff, whitespace checks and bundled-language validation.

[Manual-editor evidence](https://github.com/DanielP-1337/ha-speidel-braumeister/blob/3.2.1-beta.7/docs/manual-editor-hardware-2026-11-17.md)
and [delayed-start/countdown evidence](https://github.com/DanielP-1337/ha-speidel-braumeister/blob/3.2.1-beta.7/docs/start-delay-hardware-2026-11-17.md).

Rollback: card beta.22, Companion beta.12, integration beta.6 and Bridge beta.4.
Stop/cancel any scheduled device operation before changing software. No live HA
installation, restart or device command is performed by publishing these releases.
