# Integration 3.2.1-beta.15 / Bridge 0.5.1-beta.13

November 18 hardware evidence: the same rest-end prompt 2910/010 reports PH at
sequence 810 and Pi at 849; the cloud acknowledgment at 880 reaches 2930/pi/000
at 882. Accept both observed source actuator combinations, retaining exact
screen/indicator and target confirmation. The PH source variant still needs HA
hardware validation.

Heating-to-boil Cancel is now directly observed: sequence 996 key 1,
3010/PH/000 -> 998 3010/ph/120. Select at 1031 resumes to 1033 3010/PH/000.
Implement these exact pause/resume transitions. A later Select at 1118 opens
the temperature editor (3010/PH/00T, ADUS), which remains separate open work.

Use Companion beta.21 and Card beta.33. No real device commands were issued by
the development agent. No generic final abort, editor or lid-warning pause is added.
