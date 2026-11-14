Recipe navigation recovery (coordinated test release).

The observed device reports status field 8 as 1 while nine stored recipes are available and selection moves to slot 1. The old Companion discarded that selection and the old Bridge used the same field to bound navigation.

- Display Card 0.7.0-beta.22 keeps the configured device recipe list visible when the Companion snapshot is temporarily absent; it does not invent a selected slot.
- Companion 0.1.0-beta.11 validates the selection against stored recipe slots instead of status field 8.
- Bridge 0.5.1-beta.2 uses a validated contiguous stored recipe list for navigation bounds and command confirmation on the recipe-selection screen. Recipe upload count handling remains unchanged.
- Integration 3.2.1-beta.2 packages the coordinated Bridge release; integration runtime code is unchanged.

Update the Bridge app first, then the Companion and integration in HACS, restart Home Assistant, and update/reload the card. Keep the existing entities.recipes mapping from Card beta.21. Preserve all Bridge options.

HACS does not install HA apps. For the local Bridge app, extract Braumeister-Bridge-0.5.1-beta.2.zip into the addons share, replacing the braumeister_bridge directory, rebuild the app, and verify version 0.5.1-beta.2. Updating the integration alone does not update the Bridge.

Regression coverage includes all nine selected slots with status count 1, malformed navigation bounds, and a missing Companion response with a complete HA recipe list. Hardware verification of this coordinated fix is pending. Test Up/Down and the highlight first; selecting a recipe advances the device screen.
