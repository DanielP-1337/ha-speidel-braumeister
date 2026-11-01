# 2.0.11-beta — Fix RTC diagnostic entity registration

Fixes Home Assistant rejecting both RTC entities with `entity_category must be a valid EntityCategory instance, got diagnostic`.

- Use `EntityCategory.DIAGNOSTIC` for RTC offset and RTC warning.
- Regression test checks enum type and identity for both descriptions, rather than string equality.
- Clock display and RTC monitoring calculations remain unchanged.

Install through HACS and restart Home Assistant. The device diagnostics should then contain RTC offset and Check RTC (German: RTC-Abweichung and RTC prüfen). Initial values may be unknown until fresh advancing samples arrive. No automatic notification is created.

Validation: Python regression suite and dashboard tests. Actual HA registration must be confirmed after installation; the offline boundary test uses a typed enum double.
