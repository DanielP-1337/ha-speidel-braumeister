# Braumeister Bridge

Receives the data your Speidel Braumeister sends to the My Speidel cloud, directly in Home
Assistant. The Speidel Braumeister integration then reads the status locally, about once per
second instead of via the web interface. The data is still forwarded to My Speidel, so the
app and the web interface keep working.

Works with Braumeisters with the WiFi module and firmware 1.1.27.

## How it works

The Braumeister looks up `api2.myspeidel.com` via DNS when it connects. This app

1. runs a small DNS server that answers this one name with the Home Assistant IP and forwards
   all other names to your normal DNS server,
2. receives the Braumeister's messages on port 80 and forwards them to My Speidel,
3. passes every other request on port 80 to another service if you configure one (see below),
4. provides the latest messages to the integration on `127.0.0.1:8642`.

## Setup

1. Install and start this app.
2. On the Braumeister, open the WiFi settings and set the **DNS server** to the IP address of
   your Home Assistant. Only the Braumeister uses this DNS server; the rest of your network is
   not affected.
3. Switch the Braumeister off and on again. It only looks up the server address when it
   connects.
4. The app log shows `DNS api2.myspeidel.com from <Braumeister IP>` and the integration starts
   using the local data (debug log: `Got data via Braumeister Bridge`).

## Port 80 is already in use

The Braumeister always connects to port 80. If another service on your Home Assistant host
already uses port 80, move it to another port and enter it as `passthrough_url`. The app then
forwards every request that is not from the Braumeister to it.

Example for `emulated_hue` (Alexa expects it on port 80):

```yaml
emulated_hue:
  listen_port: 8300
  advertise_port: 80
```

App option: `passthrough_url: http://127.0.0.1:8300`

## Options

| Option | Default | Meaning |
|---|---|---|
| `bridge_ip` | auto | IP returned for `api2.myspeidel.com`. Auto-detected from the host. |
| `cloud_host` | `api2.myspeidel.com` | Hostname the Braumeister talks to. |
| `forward_to_cloud` | `true` | Forward messages to My Speidel. If `false`, or if the cloud is unreachable, the app answers itself and My Speidel shows the device as offline. |
| `upstream_dns` | auto | DNS server for all other names. Auto-detected from the host. |
| `cloud_dns` | `[]` | Host resolver by default; explicitly set DNS servers without the local rewrite when needed. |
| `dns_port` | `53` | Port of the DNS server. `0` turns it off (if you use your own DNS). |
| `http_port` | `80` | Port for the Braumeister's messages. Must be 80 for a real device. |
| `passthrough_url` | empty | Where other requests on port 80 go, e.g. `http://127.0.0.1:8300`. |
| `api_port` | `8642` | Local status API for the integration (only reachable from the host). |
| `log_level` | `info` | `debug` logs every message. |


## Cloud DNS and AdGuard rewrites

The built-in DNS remains enabled on `dns_port: 53` by default. For an existing
AdGuard (or other DNS) rewrite of `api2.myspeidel.com` to the HA host, set
`dns_port: 0` to disable only the bridge's DNS listener. The device must actually
use that DNS server; some routers use a separate resolver on guest Wi-Fi.

By default, `cloud_dns: []` uses the host resolver. In the documented setup,
only the Braumeister uses the bridge's DNS, so no separate cloud resolver is
needed and no third-party DNS service is selected by the bridge.

For a network-wide AdGuard rewrite with `dns_port: 0`, configure `cloud_dns`
with a reachable DNS resolver that does not apply the local rewrite. For example,
`cloud_dns: ["1.1.1.1", "1.0.0.1"]` explicitly opts into Cloudflare; choose a
resolver permitted by your network and your DNS/privacy preferences instead if
appropriate. Outbound DNS to the configured resolver must be allowed.

Both resolver modes reject non-public answers to prevent forwarding loops. The
error message points to `cloud_dns`; failure retains the existing local response
behavior. `upstream_dns` still serves the built-in DNS forwarder for other names.
HTTP passthrough still uses the host resolver, so local targets continue to work.
Cloud redirects are not followed.

Cloud requests ask for identity encoding; gzip and both zlib-wrapped and raw
HTTP deflate responses are decoded if the server compresses anyway. Recipe
persistence and the device command-response format are unchanged.

With `control_enabled: true`, local API clients can POST JSON containing
`device_id` and `action` to `/api/control`. Supported actions:

| Action | Screen transition |
| --- | --- |
| `open_settings` / `close_settings` | 101 ↔ 8101 |
| `open_manual` / `close_manual` | 101 ↔ 4006 |
| `open_recipe_list` / `close_recipe_list` | 101 ↔ 6010 |
| `open_recipe_selection` / `cancel_recipe_selection` | 101 ↔ 2015 |
| `recipe_down` / `recipe_up` | 2015, change highlighted slot |
| `pump_on` / `pump_off` | 4006, `ph → Ph` / `Ph → ph`, requires `manual_pump_enabled` |
| `heater_on` | 4006, `ph → pH`, requires `allow_remote_heating` |
| `heater_off` | 4006, `pH → ph`, `Pi → Ph`, or `pi → ph`, requires `allow_remote_heating` |

Both actuator options default to false and also require `control_enabled`.
The manual-mode keys toggle their respective actuator. This beta accepts
only the tested single-actuator transitions. Use the heating option only
for supervised tests below the setpoint and stop heating at the device.

On November 4, 2026, a hardware test of `0.3.2-control.3-beta.1` confirmed
all four actions through the local Bridge API in manual mode (`4006`).
The pump was observed starting and stopping with the heater off. On the
first pump-off attempt, the client-side status check stopped the request
before submission. The next attempt used a fresh `Ph` status and succeeded.
With the pump off, at 20 °C measured and a 38 °C setpoint, total device
power was 1,903.31 W during heating and 2.85 W after `heater_off`.

A separate manual-mode observation with a 26 °C setpoint and the pump running
showed `PH → Pi` at 26.0 °C, `Pi → PH` at 25.5 °C, and `PH → Pi` again at
26.0 °C, with no new heater command reported. During the first pause, HA
showed the pump on and 11.87 W total device power. In this run, `Pi` was a
regulation pause from which heating resumed automatically. The reported
temperatures are observations from this run.

A follow-up MySpeidel run with a 42 °C setpoint showed that `$k=2` changes
the pump flag independently while the heater is active (`PH ↔ pH`) or
paused (`Pi ↔ pi`). Above the setpoint, `$k=3` produced `ph → pi` when
enabling heat with the pump off. Disabling heat during a pause produced
`pi → ph` with the pump off and `Pi → Ph` with the pump still running.
After disabling heat, the device still reported `Ph` at 40.5 °C with the
42 °C setpoint. A new `$k=3` command changed `Ph → PH` at the same reported
temperature with the pump running. The automatic restart temperature at
this setpoint was not measured. These additional transitions were observed
through MySpeidel. Local Bridge API control of those states remains untested.

List navigation requires a known four-slot recipe list. Confirmation checks
the expected highlighted slot, including wraparound.

The Bridge requires recent status with both actuators off. HTTP 202 means the
action is queued. Only one action can be pending across the Bridge.

The Bridge adds the key once on a fresh matching device poll with the
standard successful cloud acknowledgment. Other cloud responses pass through
as received by the normal forwarding path. GET `/api/control` returns the
latest action's outcome. A later device poll reporting the expected screen
and actuator flags marks it confirmed. An action expires after five seconds
in the queue or becomes unconfirmed after five seconds awaiting telemetry.
