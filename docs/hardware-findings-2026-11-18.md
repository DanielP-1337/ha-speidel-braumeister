# Hardware observations: resume, progress, and audio

User-operated Braumeister 20L Plus, firmware 1.1.27, November 18, 2026.
The new App Store Bridge recorded these transitions. No agent sent brewing commands.

| Action | Before (state / actuators / indicator) | First confirmed result |
| --- | --- | --- |
| MySpeidel Select during purge pause | 2310 / ph / 120 | 2310 / ph / 000 |
| MySpeidel Select during first-rest pause | 2810 / ph / 120 | 2810 / PH / 000 |

The purge case was recorded at sequences 1409 → 1411; alternating purge states
2300/2310 followed, then heating state 2410 at sequence 1457. The first-rest case
was recorded at sequences 2088 → 2090. In both cases field 13 changed from A00F
to A000 and Select was key 4. These sequences belong to the post-migration
recording; private raw logs are retained locally and are not published.

Resume is now allowed only for evidenced paused states 2300, 2310, and 2810,
with actuators ph and indicator 120. Existing administrator, fresh-state,
program-control, remote-heating, and browser-confirmation gates remain.
Resume in heating state 2410, pump break 2820, and other stages remains unverified.
Up/Down in the malt-added prompt still needs a physical-key test.

The user confirmed sound playback on notebook, phone, and tablet. The old card
played once; the device and MySpeidel repeated until acknowledgment. The new
card repeats at six-second intervals while the reported alarm/pause persists,
with an optional one-shot mode and local sound mute (not a process command).

MySpeidel's yellow header progress is visible during heating. The existing
integration decodes field 12 against a full scale of 318 into percentage progress.
The card now uses that progress entity for its existing black header divider.
It does not estimate progress from temperature or elapsed time.

## Follow-up hardware validation (November 18, 2026, Europe/Berlin)

Tested release set: Bridge 0.5.1-beta.8, Menu Companion 0.1.0-beta.16,
Display Card 0.7.0-beta.26. The following are user-reported hardware results
and supplied screenshots; they are not additional independently decoded captures.

- Repeating sound continued while the notification/pause was active.
- Resume from the screen labeled **Mash rest 2** worked through Home Assistant,
  including the confirmation dialog warning that the pump and heater may restart.
  The subsequent screenshot showed the running second rest and active P/H indicators.
  Do not infer a new numeric state code or authorize every rest from that label alone.
- The user explicitly confirmed that sound stopped after resuming.
- **Mute sound** worked. It silences the local audio only; it does not acknowledge
  a device alarm, resume the program, or abort it.
- The yellow progress fill was visible inside the existing black header divider.

### Muting versus acknowledging

At 12:38 the screenshot still showed **Automatic process paused**, the red frame,
and the alarm banner after Mute sound. This is expected: the device remained
paused. The Mute sound button disappeared, while Cancel and Select remained.
The alarm display must not be cleared merely because local audio was muted.

A different screenshot, after Resume at 12:31, showed the running rest without
the red frame, but still showed the alarm banner and Mute sound. Audio had stopped,
as explicitly confirmed by the user. Retain this as an unresolved display/state
synchronization observation; the screenshot alone does not establish whether
the alarm entity was still on, the UI was stale, or a later update cleared it.
Do not conflate this with the expected alarm display after muting a paused device.

Sound output on notebook, phone, and tablet was confirmed before this follow-up.
Repeating audio and mute were confirmed afterward, but not separately on all
three device classes. Browser-specific background playback remains unverified.

These are documentation-only follow-up results; no additional device control,
runtime change, or deployment was performed to record them.
