# RepairLab: Track C foundation

Current scope: deterministic CPU CTC alignment from acoustic-model log probabilities, a local Wav2Vec2 real-audio adapter, independent manual-boundary scoring, source metadata gates and strict speaker/text holdout checks. A model and one real archive clip have been run on CPU; word timing accuracy remains unvalidated, no speech dataset is approved, and no delivery scores exist. See docs/REPAIRLAB_AUDIO_SMOKE.md and docs/ALIGNMENT_ANNOTATION.md. This is not an end-to-end speech analyzer or submission-ready build.

## Setup and checks

Python 3.12:
```sh
python -m venv .venv
.venv/bin/pip install -r repairlab-requirements.txt
.venv/bin/python -m unittest discover -s tests -v
```

Alignment CLI (requires real emissions from a separately validated model):
```sh
.venv/bin/python -m repairlab.align emissions.npy transcript-token-ids.json --duration 12.5 --blank 0
```

NPY input is log probabilities with shape `[emission_frames, vocabulary]`; JSON is a nonblank transcript-token ID array. Duration must correspond exactly to the analyzed audio. Output token spans use uniform frame spacing; validate the model's stride, receptive-field offset and manually labelled boundaries before claiming timing precision. Forced alignment can force an incorrect transcript onto plausible acoustic frames; a finite path is not transcript verification or calibrated confidence. The algorithm currently stores O(time x transcript length) backpointers and is intended for short excerpts. No audio-upload server exists yet.

## Source gate

`validate_source` requires source/rights URLs, recording/speaker/text IDs, review date, baseline suitability rationale and affirmative rights-review/derivative/redistribution flags. These are assertions supplied by the reviewer, not automatically verified legal permissions. Fictional example metadata appears only in tests; it does not approve real recordings. Do not publish recordings until recording-specific rights have been checked.

Research checked 2026-10-07:
- NASA media policy is a candidate source-policy lead, not approval of any selected recording: https://www.nasa.gov/nasa-brand-center/images-and-media/ . Check third-party content and other restrictions individually.
- Library of Congress directs users to item-level rights statements: https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/ . Hosting alone is not permission.
- Candidate English acoustic model: https://huggingface.co/facebook/wav2vec2-base-960h . Model card lists Apache-2.0 and 16-kHz speech input. This verifies a model candidate, not downloaded weights, CPU speed or alignment quality.
- Independent transcript lead: W3C hosts the same historical excerpt plus a separate HTML transcript as ACT test material. Its repository licenses documents under the W3C Document License, but recording-specific redistribution/derivative rights remain unclear, so the audio is not approved for the public dataset. Details and checksums are in docs/REPAIRLAB_AUDIO_SMOKE.md.

## Readiness checklist (0/6 complete; foundation underway)

1. Approved, suitable reference speeches plus real-audio alignment with measured boundary error.
2. Contrastive dataset: transcript-matched flaws, severity gradient, exact transformed timestamps, licensed data and frozen speaker/text splits.
3. Feature extraction, normalized detector, reproducible rubric and mathematically grounded explanations.
4. Working upload dashboard, baseline/participant overlay, evidence playback and uncertainty.
5. Held-out evaluation: naive baseline, IoU/timing error, type confusion, harmless gain/pitch controls, alternate injection methods, feature/normalization/alignment ablations; optional human recordings separately reported.
6. Fresh-clone reproduction, <=6-page technical report, 3-10 minute English/subtitled video, submission checklist and human final review.

Internal package target: 2026-10-13, conditional on source and alignment gates. Official deadline verified 2026-10-07: October 15, 2026 at 00:15 IST, https://multimodal-ai-hackathon-2026-7.devpost.com/details/dates . Final registration/terms/submission stay human-controlled.

Repair previews are optional sanity checks after the required pipeline. Never claim injected-flaw localization establishes listener comprehension or clinical benefit. Maintain a separate unseen-corruption test; the detector must not read injection labels or parameters. All derivatives of a source recording remain in its partition.

## Test report: 2026-10-07

Initial core: Python 3.12 / NumPy 2.3.5, 7/7 tests passed on handcrafted emissions and fictional provenance metadata. Acoustic adapter increment: NumPy 2.5.3, 10/10 tests passed including PCM loading and transcript checks. Current increment: Python 3.12 / NumPy 2.3.5, 14/14 tests passed, adding strict human-reference provenance, subset coverage and median/p95/max boundary-error calculations. One real-audio smoke run completed, separately reported in docs/REPAIRLAB_AUDIO_SMOKE.md; no manual word-boundary accuracy or delivery-performance result is available. `git diff --check` passed.
