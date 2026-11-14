# Local-mode hardware feedback, November 14, 2026

Test combination: Integration 3.2.1-beta.3, Companion 0.1.0-beta.12,
Display Card 0.7.0-beta.22 and Bridge 0.5.1-beta.2. The user enabled local-only
mode and reported restarting the Bridge after the configuration change.

## Observations reported by the tester

- Recipe Up/Down and the selected highlight update immediately to the tester.
- When navigating recipes from the phone, the tester observes the selected
  recipe changing simultaneously on the phone and PC Display Cards.
- Switching to manual control and pump/heater on/off feedback is responsive.
- During the brewing process, the user also reports a substantial improvement
  in responsiveness compared with the previous polling behavior.
- Standing next to the brewer and controlling it through HA on a phone, the
  tester observes the physical display and Display Card switching screens
  almost synchronously. The physical display visibly redraws line by line,
  from top to bottom. This is a visual observation without synchronized timing.
  It suggests distinguishing the start of a screen change from completion of
  the device's redraw; it does not identify whether CPU, firmware, display bus
  or display controller limits that redraw.
- The supplied screenshot at 09:08 CET shows a paused mash-in screen, an alarm,
  target/actual temperatures of 38/12 °C and a confirmed menu action. It does
  not by itself measure latency or validate every brewing stage or control.

These are qualitative hardware observations, not timed latency measurements.
A full internet-disconnected test including HA/Bridge restart remains open.

## Follow-up: WAN disconnected and brewer cold start

The tester subsequently reported the following with `forward_to_cloud: false`
after installing integration beta.4 (the active version was not re-read during
this test). MySpeidel stopped updating and showed the brewer offline with its
last known state.

With the Speedport WAN cable physically disconnected, the existing local
connection continued to support these operations without reported problems:

- Manual mode to/from the main menu.
- Pump on/off and heater on/off.
- Starting recipe selection, recipe Up/Down and confirming the selection.
- Reaching the "Water filled?" prompt; testing stopped there. Continuing beyond
  this prompt or completing a brewing cycle was not validated.

After powering the Braumeister off and on while WAN remained disconnected,
no new connection was established. Thus continued operation across WAN loss
is demonstrated by the tester, but offline cold-start/reconnection is currently
failing. The layer responsible is not yet identified. HA/Bridge restart while
offline remains a separate unverified case.

Next investigation: correlate brewer Wi-Fi/DHCP registration, assigned DNS,
AdGuard queries/responses (including A/AAAA and any additional startup domains),
local DNS routing and Bridge request timestamps during an offline cold start.
Check for client-specific rules affected by a changed address, external DNS
fallback, or firmware startup dependencies. Do not assume AdGuard or NTP is the
cause without observing the traffic. Record how long each attempt was observed.

### Recovery after router restart with WAN restored

The tester restarted the Speedport with the WAN cable connected and internet
available. The Braumeister then reconnected to HA. After the tester confirmed
water was filled on the physical brewer, the process continued; the supplied
screenshot shows HA at "Pump is being purged" (20:33) while MySpeidel retains
the old manual-mode state (20:01). MySpeidel remained offline/stale.

Router restart and WAN restoration occurred together, so this does not establish
that internet access itself was necessary for recovery. WLAN/DHCP/DNS recovery
following the router restart remains an alternative explanation. No additional
brewer restart was reported in this recovery step. Offline wait duration and
recovery timing were not supplied.

### Speedport limitation and phone observation

The tester clarified that their Speedport Smart 4 explicitly requested a manual
restart on its built-in display after checking/reconnecting the WAN cable; it
did not restore the connection automatically in this test. Simply reconnecting
WAN without a router restart is therefore not a useful control in this setup.
This is a report of the observed setup, not a verified claim about every
Speedport Smart 4 firmware/configuration.

The tester also could not open/use the HA Companion app on their phone while
connected to Wi-Fi with WAN unplugged. No error message, selected app URL or
direct-LAN-IP browser result was recorded. This may share a local network/DNS
cause with the brewer reconnection failure, or be a separate app routing issue
(external URL, home-network recognition, or phone network selection). It does
not establish that HA or the Bridge requires internet access.

## Open community validation tasks

- [ ] Repeat WAN-loss operation on another router/network; record component
  versions, controller/firmware, DNS routing and observation durations.
- [ ] Test a brewer cold start with WAN denied while WLAN, DHCP and local DNS
  remain stable (for example, a router/firewall that supports per-device WAN
  blocking). Capture network registration, DNS queries/answers and the first
  Bridge request, or identify the step where progress stops.
- [ ] Restart HA and the Bridge independently with WAN denied; confirm recovery
  without cloud authentication and without a prior cached cloud connection.
- [ ] Compare the phone app with access through the HA LAN IP in a browser;
  record the app's internal/external URL and home-network recognition. Test
  hostname resolution separately and note whether the phone stays on Wi-Fi.
- [ ] Validate later brewing stages and recovery separately; the disconnected
  hardware test above stopped at the water confirmation prompt.

The current evidence supports continued local operation across WAN loss, not
yet reliable end-to-end cold startup without WAN. Community reproductions are
welcome; no cause-specific code fix is justified by the current evidence.

## TODO: compare reaction times with the controller generation from 2021

- [ ] Identify an available newer controller and record model, hardware revision,
  firmware, network connection and supported local protocol before comparing.
- [ ] Measure both controller generations under comparable network conditions
  and HA/Bridge/card settings, using normal, already-supported operations.
- [ ] Separate command submission, delivery in a device poll, device status
  confirmation, HA entity update and card rendering timestamps. Also measure
  spontaneous status changes during brewing, independently of button presses.
- [ ] Record both displays together on video and distinguish the first visible
  change from the fully drawn screen, especially on the older device's display.
- [ ] Record device message intervals and repeated measurements (sample count,
  median, 95th percentile and maximum), rather than only perceived speed.
- [ ] Determine whether any difference comes from firmware/controller processing,
  the Wi-Fi module, protocol cadence, network latency or HA polling.

The tester suspects the older controller's MCU (identified by the tester as a
32 MHz ATxmega256A3) may now be the limiting factor. This remains a hypothesis;
neither the clock rate alone nor the current responsiveness establishes the
bottleneck. No claim that the newer generation is faster has been verified.
