# Direct water confirmation, Cancel, and alarm notifications

Display Card **v0.7.0-beta.25**, Companion **v0.1.0-beta.15**, integration
**3.2.1-beta.9**, Bridge **0.5.1-beta.7**.

At the initial Water added? prompt, Cancel, Up and Select are available;
Down remains disabled. Select directly starts pump purging after the water
confirmation, without requiring a delayed start. Start permissions remain
required; Cancel does not require program-start or remote-heating permission.
Fresh connection, admin access and control_enabled still apply.

Cancel is also routed from the alternating purge/pump-pause screen 2310.
The first Cancel requests a pause (indicator 120); Cancel in that paused state
requests final abort. Resume remains limited to the previously mapped 2300.
Unknown states remain disabled. These new paths need hardware confirmation;
synthetic tests do not establish actual device behavior. Commands are never
automatically replayed if a screen changes or confirmation is missing.

## Sound setup in the card editor

Open Edit dashboard -> Edit card -> Alarm sound. Enable Sound on alarm / pause,
choose volume and use Test / enable sound. Leave the URL blank for a synthesized
tone, or enter your own HTTP(S) URL or HA path such as /local/sounds/alarm.mp3
(file stored at /config/www/sounds/alarm.mp3). No MySpeidel audio is included.
The controls and messages are translated into all eight bundled languages.

Sound is off by default and plays once per new alarm/pause, for at most five
seconds, on the browser displaying the card. Ordinary Cancel does not cause
a sound unless the device reports a pause/alarm. Existing alarms on page load
or reconnection are not replayed. Use the card's Test / enable sound button on
the FireHD after opening the dashboard; blocked/failed audio is shown visibly.
Browser autoplay and background restrictions still apply, so a sleeping/closed
tablet is not a reliable alarm endpoint.

## Hue and other HA notifications

Import [the notification blueprint](https://github.com/DanielP-1337/braumeister-display-card/blob/v0.7.0-beta.25/blueprints/braumeister-alarm-light.yaml)
under HA Settings -> Automations & scenes -> Blueprints -> Import blueprint.
Create an automation, select the alarm, step and connection entities used by
the card, and your RGB Hue lights. No entity IDs need editing in YAML.
Lights blink three times in the configured color (normal brewing prompts: green by default; pause/unclassified alarm: red by default), then their previous state is restored. Use only
RGB-capable lights and avoid concurrent automations controlling the same lights.
The optional action selector supports other notifications/media players.
This automation runs on HA even if the dashboard is closed. A HA restart or
manual automation interruption during blinking may prevent state restoration.

## Install and test

Update/rebuild the separate Bridge app from the attached beta.7 ZIP while idle,
preserving its options; HACS does not update the Bridge app. Update all three
HACS prereleases above, restart HA and reload the dashboard. Integration beta.9
is a coordinated release marker with unchanged integration runtime code.

Test initial Cancel, then direct Select with water filled and device ready.
Check Cancel during purge and its pause/abort distinction. Test alarm sound on
the tablet and the Hue automation separately. No live device commands, light
changes or HA configuration changes were performed during development.

The previous HA countdown Start now path was confirmed by the user; subsequent
purge cancellation in that earlier trial was performed through MySpeidel.

References: [browser autoplay](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Autoplay),
[HA selectors](https://www.home-assistant.io/docs/blueprint/selectors/),
[scene snapshots](https://www.home-assistant.io/integrations/scene/).

## Mash-in sequence and notification colors

The captured cloud Select transitions are now mapped individually:
2510 / Pi / 010 -> 2610 / ph / 000 (temperature notification acknowledged),
2610 / ph / 000 -> 2705 / ph / 000 (open Malt added? confirmation), and
2705 / ph / 000 -> 2810 / PH / 000 (start the first rest).
The last transition requires start/heating permissions and an explicit confirmation.
Cancel is available at these prompts and in rest/pump-pause states 2810/2820;
it first requests program pause and only a second confirmed Cancel requests abort.
These newly enabled HA paths still need hardware testing. Resume remains limited
to its previously mapped state. Other unverified later process states are unchanged.

The user's existing HA Start now and purge Cancel/abort at 2300 are confirmed by
local_control records. Cloud purge-pause Cancel/abort at 2310 is also recorded.
Confirming delay selection at zero can lead directly to 2300; the Bridge now
accepts that exact alternative without falsely confirming unrelated states.

Normal notifications (mash temperature reached, rest end, hop addition, brew
finished) have a configurable Hue color, default green. Pause or unclassified
alarm uses a separate configurable color, default red. Both can play the
chosen tablet sound. The card labels known normal notifications as a notice.

TODO: Up/Down on Malt added? (2705) had no recognizable effect via MySpeidel.
Test directly on the device and correlate fields before enabling either arrow.
Do not infer a temperature, timer or recipe edit from a successful HTTP response.

Validation: 373 core tests plus 280 subtests, 61 Companion tests, all 11 card suites, Ruff, and the notification blueprint's HA schema validation passed.
