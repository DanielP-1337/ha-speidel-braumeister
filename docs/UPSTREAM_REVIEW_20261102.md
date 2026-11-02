# Upstream review and publication checkpoint, 2026-11-02

## Scope and basis

Upstream `omphteliba/ha-speidel-braumeister/main` was checked at
`7a2f6fd724f03c48da7ae406609edbf9d788d382`, including merged PR #15. The existing
fork main remains at `2bcfc86bd686118f88fdde1cf70ca1ee95644cda` at this checkpoint.
This publication branch starts from the checked current upstream, not fork main.
It is not a released version, a HA installation change, or a working remote
control API.

The original local development head `1c76547` was tested with `git merge-tree
--write-tree` against the current upstream. Result: no textual conflicts;
merged tree `afde5078c1fa954893bd906f5b56df78c43648e6`. Its cumulative additions
were applied in a separate worktree so original commits, worktrees and paused
backport changes remain intact. The publication uses two reviewable commits
rather than carrying the intermediate experimental/deployment history.

The recorder app Git blobs match the previously tested Bridge 0.3.1-diag.1
source. Recorder defaults remain disabled, 8 MiB per file, four retained files.
Upstream `custom_components`, workflow files and test requirements are unchanged.
Bridge and HA integration versions remain separate. No device-command endpoint,
automatic actuator action, replay facility or command queue was introduced.

## Current local validation

- Windows AMD64, Python 3.11.2, pytest 9.2.0, pytest-asyncio 1.4.1.
- Complete suite on this upstream-based tree: **282 passed, 1 skipped,
  261 subtests passed, 50.81 seconds**.
- The skipped test requires POSIX filesystem permissions, unavailable on Windows.
- Ruff and staged/working diff whitespace checks passed.
- Initial sandbox execution stalled in asyncio's local socketpair creation;
  the completed suite ran outside that sandbox. No real cloud/device requests
  or HA operations were part of these tests.
- Upstream's tzdata requirement was supplied in an isolated test directory;
  requirements and shared Python installation were not changed.
- One real checkout problem was corrected: Windows CRLF conversion invalidated
  the exact-source reference SHA256 test. `.gitattributes` now fixes LF for
  `tests/fixtures/bridge_030.py`; the expected original hash was retained.

Previous ARM64-emulation build/synthetic smoke results remain historical results
in `RECORDER_030_VALIDATION.md`; they were not rerun or counted as new tests here.
Physical-device recorder exports and navigation observations are documented in
`COMMAND_RE_EXPERIMENTS.md`. A future GitHub workflow result is separate from the
completed local results above.

## Publication contents and privacy

Only reviewed source, synthetic tests, public upstream reference code and
sanitized documentation are included. Private backups, capture JSONL, HAR,
credentials, cookies, real device identifiers, active private options and SSL
files remain outside this branch. Personal Windows backup paths in the copied
historical plan were replaced with `<LOCAL_BACKUP_DIR>` placeholders.

Deployment/validation plans are historical checkpoints, not instructions to
install this branch automatically. Restore procedures remain untested. The
ongoing HA setup is unchanged by publication; no repository switch, add-on
update, DNS change, restart or new device test is authorized by this document.

## Recommended contribution route

Keep development in the existing fork on feature branches. Offer a focused
upstream PR for the optional recorder, fault isolation and tests, and another
for validated protocol/navigation documentation if the maintainer prefers
separate review. Do not present the observed context-dependent keys as an
unconditional pump/heater API or a production-ready local remote control.

Navigation evidence currently covers main-menu entries/back paths and selected
recipe-list movements, including four-slot wraparound. Recipe confirmation,
actual program start, actuator control, firmware-independent semantics and
cloud queue/retry behavior remain outside the confirmed scope. The three-click
entry anomaly is recorded, with its cause unresolved.

No upstream PR, release, tag or default-branch update is part of this checkpoint.
An independent repository is unnecessary while the contribution remains closely
coupled to this integration and Bridge. Reassess only if a separate product or
maintenance model becomes necessary.
