# VCTK CPU alignment smoke — 2026-10-07

## What ran

The official VCTK 0.92 range fetcher retrieved `p225_001`, `p226_001` and `p227_001` (mic1) from three speakers. Each transcript is “Please call Stella.” The original 48-kHz FLAC files were decoded to mono 16-bit 16-kHz PCM and aligned with the pinned `facebook/wav2vec2-base-960h` snapshot `22aad52d435eb6dbaf354bdad9b0da84ce7d6156` on CPU with two torch threads.

| Recording | Duration | Adapter elapsed including model load | Predicted PLEASE | Predicted CALL | Predicted STELLA |
|---|---:|---:|---:|---:|---:|
| p225_001 | 2.051500 s | 0.351 s | 0.3017–0.6436 | 0.8850–1.1263 | 1.2269–1.5487 |
| p226_001 | 2.798688 s | 0.430 s | 0.9262–1.2282 | 1.3289–1.5302 | 1.6309–1.9530 |
| p227_001 | 3.428750 s | 0.502 s | 0.9625–1.2231 | 1.3434–1.6241 | 1.8247–2.1655 |

The model emitted the same warning as the prior NASA smoke: `wav2vec2.masked_spec_embed` was newly initialized. Evaluation/inference mode was used. These elapsed values are single local measurements and are not a benchmark.

## What this proves—and does not

This proves the source fetch, decode, model inference, transcript tokenization and CTC alignment path executes for three licensed real recordings with different speakers. It does not prove timestamp accuracy. Spectrograms were inspected without consulting the predictions first, but no supported audio playback or independent human auditory annotation was available in this execution. Therefore no boundary-error number is reported and readiness milestone 1 remains open.

CTC token activation spans may be narrower than perceived whole-word boundaries, especially around unvoiced consonants and inter-word silence. The manual protocol must score exactly what the UI intends to display; if the UI needs full word intervals rather than token-evidence cores, that distinction must be implemented and evaluated explicitly instead of relabelling these spans.

Raw audio, converted WAVs, spectrograms and full alignment JSON remain private and uncommitted. Source checksums and attribution are in docs/REPAIRLAB_SOURCES.md. Next: independent auditory labels with prediction timestamps hidden, followed by `python -m repairlab.evaluate_alignment` and a recorded median/p95/max boundary-error report.
