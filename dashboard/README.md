# Braumeister display card · 0.2.0

Optional native Home Assistant dashboard card inspired by the Braumeister display. It reads Home Assistant entities, with no iframe, MySpeidel cookies, frontend cloud credentials, or additional JavaScript libraries. The current interface labels are German.

## Install

1. Copy `braumeister-display-card.js` to the `www` directory next to your Home Assistant `configuration.yaml`. This is usually `/config/www/`; File Editor may display it as `homeassistant/www/`. If you create `www` for the first time, restart Home Assistant.
2. Add `/local/braumeister-display-card.js?v=0.2.0` as a **JavaScript module** in dashboard resources. Resource management may require Advanced Mode in your user profile.
3. Reload the browser, add a manual card and paste [example.yaml](example.yaml).
4. Replace every example entity ID with your actual IDs from Developer Tools → States. IDs are not discovered automatically. In a Sections dashboard use the full section width.

Installing the integration through HACS does not automatically install or register this optional frontend file. No changes to Python code are required for the card itself.

Upgrading the earlier personal 0.1.0 card: explicitly map all entities in YAML before replacing the JavaScript file. Version 0.2.0 removes the personal entity defaults. Keep a copy of the old file to roll back.

## Entity mapping

| Key | Entity / meaning |
| --- | --- |
| temperature, target | Current and target temperature in °C |
| step, recipe | Current step and recipe name |
| mode, connection | Device mode and connection status (`online`) |
| pump, heater | Reported actuator status (`Ein` / `on` lights the badge) |
| progress, time | Reported progress (%) and time (minutes) |
| alarm | Alarm binary sensor |
| plug | Optional power-plug switch |
| power | Optional total power sensor in watts |
| behavior | Optional plug power-on-behavior select |

Omit optional plug entities when not present; the corresponding unavailable controls are disabled. Missing/unknown sensor values are displayed as a dash. Temperatures are hidden when connection is not `online` or the configured plug reports `off`.

## Views and limits

- **Display:** target/current temperature, phase, recipe and alarm.
- **Rezept:** current recipe, step, reported progress and time. No fabricated recipe list or mash schedule. The time value is not independently verified as remaining time.
- **Strom:** actual `switch.turn_on` / `switch.turn_off` calls for the configured plug, plus `select.select_option` using the options supplied by HA. This switches the entire Braumeister power supply.
- **Status:** connection, mode and reported pump/heater states. The P/H badges open entity details.
- The yellow device-control buttons are deliberately disabled. This card does not start a brew or control the pump/heater directly.
- Accurate actuator telemetry requires the XHR parser correction in [PR #8](https://github.com/omphteliba/ha-speidel-braumeister/pull/8). This frontend branch does not bundle that backend change.
- `online` reflects the integration's report, not an independent freshness or reachability check.

The display is implemented with original HTML/CSS; no Speidel JavaScript, logos or session material are distributed.

## Validation

With Node.js installed, from the repository root:

```sh
node --check dashboard/braumeister-display-card.js
node dashboard/test.cjs
```

Tests use simulated HA states and service calls; they do not contact or operate a real device. Version 0.1.0 was displayed successfully by the contributor in HA on desktop and mobile. The configurable 0.2.0 revision and equal-width/equal-height navigation rings still need validation in an actual HA browser.
