# RepairLab local review dashboard

Run from the repository root:

```bash
python -m repairlab.dashboard
```

Then open `http://127.0.0.1:8765`. Upload transcript-matched baseline and participant 16-kHz mono PCM WAV files and their independently produced forced-alignment JSON files. The page shows an energy overlay, timestamped flagged words, mathematical evidence and uncertainty notes.

The server binds to localhost by default, uses no external web assets, does not log requests, processes audio in a temporary directory and deletes it after each request. The 6-MiB request limit accommodates two permitted 60-second PCM clips after base64 expansion. This is a review interface, not a hardened public deployment.

## Current limits

- Alignments must be created before upload; model inference is deliberately not hidden inside the review request.
- Only the energy frame overlay is plotted in this first UI. Word-level explanations can include all six implemented features.
- The threshold is exposed because it is a development parameter; it has not been calibrated on held-out real delivery flaws.
- A flagged region is evidence for review, not a quality grade, diagnosis or therapeutic recommendation.
