# Changelog

## 0.3.1-diag.1 (local preparation, not an upstream release)

- Optional bounded private recorder for the verified 0.3.0 app baseline; disabled
  by default. No new polls, commands, replay, download route or integration update.
- Fault-isolated preparation/writing, binary-safe correlated events, explicit
  gaps, bounded queue/retention, owner-only POSIX files and uncertain-tail markers.
- Handle SIGTERM through the existing cleanup so normal container stop can write
  a session-end record; forced termination remains an uncertain tail.
- Local differential, ARM64 emulation and synthetic persistent-data export tests.
  See the preparation plan before any deployment or recording.

## 0.3.0

- Cloud lookups reject private/local answers, so a network-wide DNS rewrite (e.g. AdGuard
  with `dns_port: 0`) can no longer loop the bridge back to itself. New option `cloud_dns`
  for an explicit resolver in that setup; by default the host resolver is used as before.
- `dns_port: 0` is accepted (disables the DNS server, as documented).
- Deflate-compressed cloud answers are unpacked for the device; redirects are not followed.
  (thanks to DanielP-1337, #13)

## 0.2.2

- After a restart the restored recipe list was written again on the first message; now only
  real changes are saved.

## 0.2.1

- The state-change log also shows the temperature unit (field 2) and the display language
  (field 0) and logs when they change.

## 0.2.0

- The recipe list of each device is saved in the app's data folder and restored after a
  restart, so the integration can show the recipes also while the Braumeister is off.

## 0.1.3

- **Fix:** answers from the cloud reached the device gzip-compressed, because aiohttp asked
  for compression on its own. The device could not read them: recipe syncs and other
  commands were lost and it reported only every ~4 s. The bridge now asks for plain text
  and unpacks compressed answers.
- Debug log: status, duration and answer of every request forwarded to the cloud.

## 0.1.2

- Log every command the cloud sends to the device (`$k`, `$rz`, `$d`, ...), e.g. to follow a
  recipe sync.

## 0.1.1

- Log every change of state code, pump/heater flags and alarm indicator, so short
  events (e.g. a hop-addition beep) show up in the app log.

## 0.1.0

- First version: DNS answer for `api2.myspeidel.com`, receiver on port 80 with forwarding to
  My Speidel, passthrough of other port-80 traffic, local status API for the integration.
