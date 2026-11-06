# Program controls — local preparation, no HA deployment

Based on the existing experimental Bridge `0.3.2-control.3-beta.4` source.
No release version was bumped and no update package was installed. The source
must not be copied into HA as though this were an already validated release.

## Prepared transitions

| Action | Required source | Required later confirmation | Key |
| --- | --- | --- | --- |
| `select_recipe` | 2015 / ph / 000, known 4-slot list and current slot | 2030 / ph / 000 | 4 |
| `request_program_pause` | 2300, normal indicator 000, pump off/on | 2300 / ph / 120 | 1 |
| `request_program_pause` | 2410, normal indicator 000, recognized actuator flags | 2410 / ph / 120 | 1 |
| `abort_program` | 2300 or 2410 / ph / 120 | 101 / ph / 000 | 1 |
| `resume_program` | 2300 / ph / 120 | 2300 / Ph / 000 | 4 |

User-reported cloud/device observations on 2026-11-06 establish the pause dialog,
final-abort outcome and purge-resume outcome. Selecting a recipe was previously
observed as 2015 -> 2030. These are evidence for the bounded local prototype,
not proof that its local command-delivery path works on hardware.

The first Cancel requests a pause. It is **not** reported as final abort. Stage
codes alone cannot confirm pause/resume: indicator and actuator flags must also
match subsequent telemetry. Final abort and resume require the pause indicator
`120`; no generic raw-key endpoint is added.

## Permissions and isolation

All actions require `control_enabled: true`, the existing loopback-only API,
fresh matching telemetry, and the existing one-command queue. Resume additionally
requires **both** `program_control_enabled: true` and `allow_remote_heating: true`.
The new program option defaults to false. Requesting pause and final abort do
not require opting into resume/heating. Existing options and persistent data
paths are unchanged.

Source indicator, screen, flags, recipe slot and relevant permissions are checked
again immediately before dispatch. A changed pause indicator invalidates a queued
first Cancel, preventing it from becoming a second, final-abort key press.
Commands are appended once only to the existing successful cloud acknowledgement;
cloud commands take precedence and remain unmodified. No extra cloud requests,
retries, replays, DNS changes or device probes are generated.

Water confirmation, water-prompt Cancel, delayed-start Up/Down, resume at 2410,
and all transitions at 2310 remain unsupported. Do not infer those mappings from
similar button labels or expand heating permission to them implicitly.

## Local tests

Full Bridge-source suite: **220 tests and 261 subtests passed**. The new tests use
synthetic device requests and a local loopback mock cloud; no real cloud/device
or productive directories are used. Coverage includes single dispatch,
cloud-command priority, strict indicator confirmation, unknown contexts,
dialog changes after enqueueing and permission revocation before dispatch.

The matching Companion and Card branches are also local. Hardware validation,
container build/smoke testing and an explicitly released installation package
remain required before deployment. No heating, pumping or restart was initiated
by the development tests.
