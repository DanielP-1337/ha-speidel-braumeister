# Integration 3.2.1-beta.11 / Bridge 0.5.1-beta.9

- Expose verified target/elapsed time fields during boil heat-up (3010), including live edits of the target duration. These values are not a whole-brew remaining time.
- Bridge: add the recorded rest-end → malt-pipe removal → boil-start prompt → heat-up confirmations. Boil start requires program control and remote heating to be enabled.
- Add state-checked pause/abort in those three prompt states, with exact response confirmation. Hardware validation of the new stop contexts is pending; Resume in later phases is not generalized.
- Display Card 0.7.0-beta.27 uses device recipe details for the responsive Recipe tab; Menu Companion 0.1.0-beta.17 exposes the new actions.
- Boil temperature/time editors remain a documented TODO. Their appearance and the confirmed 12-minute / later 3-minute live-time edits are recorded in the card documentation.

The Bridge is distributed through the existing `#beta` HA App Store repository.
Update only after the running brew has finished. Do not run a second Bridge instance.

The observed lid-removal acknowledgment (`3010/qH/0DT` → `3010/qH/00T`) is now a separate guarded confirmation, not generic Resume. Cancel and Up/Down at that warning remain unverified and unavailable.
