# Recipe display and boil editor observations — November 18, 2026

The Recipe tab uses live step attributes for target/elapsed rest time, verified
3010 boil heat-up time, and the 2120 start-delay countdown. It does not call the
legacy integration time value a remaining time. Static schedule data comes only
from the explicitly configured same-device `entities.recipes` sensor.

Device names and cloud account names can differ. Unique exact name matches may
highlight the current stage; otherwise the local recipe dropdown is for inspection
only. Live step changes are not written back into the stored schedule. The source
currently omits zero-duration rests. No whole-brew ETA or completed-stage history
is inferred from a percentage.

Configure the existing **Device recipes** entity from the same Braumeister under
`entities.recipes` (plural). Keep `entities.recipe` mapped to the current recipe
name. Example only; replace both IDs with your installation's entity IDs:

```yaml
entities:
  recipe: sensor.my_braumeister_brew_name
  recipes: sensor.my_braumeister_device_recipes
```

On widths of at least 780 pixels, live data and the stored schedule are side by
side; smaller cards stack the sections vertically. This is the Recipe tab, not
an additional permanent sidebar on the Display tab.

## Hardware findings and TODO

- [x] Rest-end notification and audio confirmed by user.
- [x] Cloud Select at rest end: `2910/Pi/010` → `2930/pi/000` (remove malt pipe).
- [x] Cloud Select after malt pipe removal: `2930/pH/000` → `2960/pH/000` (start boiling).
- [x] Cloud Select at boil start: `2960/pi/000` → `3010/PH/000` (heat to boil).
- [ ] Validate the new HA confirmation actions on hardware with the matching beta set.
- [ ] Validate pause/abort in these later phases. Implement Resume only after its transition is established.
- [x] User confirmed the editor sequence: normal screen → Select → temperature editor → Select → time editor → Select → normal screen. Up/Down appear in the editors and disappear afterward.
- [x] Captured state 3010: normal `A00S/000`; editors `ADUS/00T` (temperature) and `ADUS/00Z` (time).
- [x] In the temperature editor, key 2/3 changed field 4 by −10/+10 (1 °C).
- [x] In the time editor, key 2/3 changed field 6 by −60/+60 seconds. User confirmed 10 → 12 minutes and later 3 minutes. Confirmed screens showed 12 / 0:00 and 3:00 / 0:00.
- [ ] Implement guarded live boil-temperature and boil-time editing: entry, up/down, progression through both editors, confirmation, limits, stale-state handling and cancellation. Check whether Cancel discards one field, both fields, or pauses the program. Do not assume manual-mode editor cancellation semantics apply here.
- [ ] Physical Up/Down behavior at the malt-added prompt remains unverified.

Evidence consists of user-operated hardware screenshots and diagnostic transitions;
no agent issued brewing commands. Stored recipe duration and live edited duration
must remain distinct in the UI.

- [x] Lid warning: cloud Select at sequence 3374 (`3010/qH/0DT`, `ADUS`) → 3376 (`3010/qH/00T`, `A00S`). The editor flag remains T; do not assume this is normal `000` or a generic Resume.
- [ ] Verify Cancel and Up/Down at the lid warning; these remain unavailable in HA.
