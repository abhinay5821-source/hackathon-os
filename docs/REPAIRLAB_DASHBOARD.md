# RepairLab local review dashboard

Run from the repository root:

```bash
python -m repairlab.dashboard
```

Then open `http://127.0.0.1:8765`. Upload transcript-matched baseline and participant 16-kHz mono PCM WAV files and their independently produced forced-alignment JSON files. The page provides both audio players; selectable energy, pitch, spectral-centroid and zero-crossing overlays; highlighted participant intervals; timestamped mathematical evidence; one-click playback of a flagged interval; and uncertainty notes.

The server binds to localhost by default, uses no external web assets, does not log requests, processes audio in a temporary directory and deletes it after each request. The 6-MiB request limit accommodates two permitted 60-second PCM clips after base64 expansion. This is a review interface, not a hardened public deployment.

## Current limits

- Alignments must be created before upload; model inference is deliberately not hidden inside the review request.
- Audio playback uses local browser object URLs. The server still deletes its temporary copies after analysis.
- Browser playback and visual usability require manual review; automated tests cover the HTTP page/upload route and required interface surfaces, not human interaction quality.
- The threshold is exposed because it is a development parameter; it has not been calibrated on held-out real delivery flaws.
- A flagged region is evidence for review, not a quality grade, diagnosis or therapeutic recommendation.
