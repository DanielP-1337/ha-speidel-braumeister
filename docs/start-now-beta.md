# Start now from the countdown

Display Card **v0.7.0-beta.24**, Companion **v0.1.0-beta.14**, integration
**3.2.1-beta.8**, Bridge **0.5.1-beta.6**.

The previously disabled countdown Select button is now labeled **Start now**.
It skips the delay and starts pump purging immediately. A dedicated localized
confirmation states that the pump starts immediately and heating may follow.
This is distinct from Cancel, which returns to the main menu.

The Bridge requires fresh state 2120 / A00S / 000 / ph, a positive valid
field-17 countdown, `control_enabled`, `program_control_enabled` and
`allow_remote_heating`. Permissions and context are checked again before send.
One `$k=4` is sent, never automatically replayed. Confirmation requires the
observed 2300 / A000 / 000 / Ph transition and field 17 reset to zero.

The card requires `menu_control: true`, `program_control: true`, an admin user
and the new Companion capability. An old Companion leaves Start now disabled.
The actual device countdown remains displayed; all eight languages are included.

## Install

Update the separate Bridge app first using `Braumeister-Bridge-0.5.1-beta.6.zip`:
extract its folder into `\\homeassistant.local\local_apps`, preserve existing
options, and rebuild/update the existing local app while the device is idle.
Then download the three HACS prereleases above, restart HA and reload the card.
The integration version is a coordinated release marker; its runtime behavior
is unchanged from beta.7. HACS does not update the Bridge app.

## Evidence and testing

On November 18, 2026, MySpeidel Select during countdown was observed on the
Braumeister 20L Plus (firmware 1.1.27): 2120 / ph / remaining 3531 seconds ->
2300 / Ph / remaining 0, with the physical/web display showing pump purging.
The earlier HA Up/Up/Select/Cancel path is hardware-verified. This new HA
Start now implementation still needs the user's hardware test. Automatic
countdown expiry and rest/boil editors remain unverified.

Only test Start now when water is filled and the device is ready for an actual
program start. No device commands or live HA changes are made by this release.

[Timestamped evidence](https://github.com/DanielP-1337/ha-speidel-braumeister/blob/3.2.1-beta.8/docs/start-delay-hardware-2026-11-17.md).
Rollback: Card beta.23, Companion beta.13, integration beta.7, Bridge beta.5.

Validation: 363 core tests and 280 subtests, 52 Companion tests, all ten card test suites, Ruff, and AMD64/ARM64 Bridge image builds and import checks passed.
