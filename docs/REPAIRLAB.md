# RepairLab: Track C foundation

Current scope: deterministic CPU CTC alignment, a local Wav2Vec2 real-audio adapter, independent manual-boundary scoring, source gates, reproducible VCTK fetching, strict holdouts, deterministic corruptions and controls, a dataset writer that separates detector inputs from evaluation truth, a transparent word-level acoustic comparison baseline, a CLI that exports pair analysis, and a local upload/review dashboard with evidence playback and selectable overlays. The pinned model has run on one NASA archive clip and three licensed VCTK calibration clips, but word timing accuracy, feature thresholds, browser interaction quality, dashboard usability and delivery scores remain unvalidated. See docs/REPAIRLAB_AUDIO_SMOKE.md, docs/REPAIRLAB_VCTK_ALIGNMENT.md, docs/ALIGNMENT_ANNOTATION.md, docs/REPAIRLAB_SOURCES.md, docs/REPAIRLAB_CORRUPTIONS.md, docs/REPAIRLAB_FEATURES.md, docs/REPAIRLAB_PIPELINE.md and docs/REPAIRLAB_DASHBOARD.md. This is not a submission-ready build.

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

NPY input is log probabilities with shape `[emission_frames, vocabulary]`; JSON is a nonblank transcript-token ID array. Duration must correspond exactly to the analyzed audio. Output token spans use uniform frame spacing; validate the model's stride, receptive-field offset and manually labelled boundaries before claiming timing precision. Forced alignment can force an incorrect transcript onto plausible acoustic frames; a finite path is not transcript verification or calibrated confidence. The algorithm currently stores O(time x transcript length) backpointers and is intended for short excerpts. The local dashboard accepts audio only after alignment; it is a review interface, not a hardened public deployment.

## Source gate

`validate_source` requires source/rights URLs, recording/speaker/text IDs, review date, baseline suitability rationale and affirmative rights-review/derivative/redistribution flags. These are assertions supplied by the reviewer, not automatically verified legal permissions. Fictional example metadata appears only in tests; it does not approve real recordings. Do not publish recordings until recording-specific rights have been checked.

Research checked 2026-10-07:
- NASA media policy is a candidate source-policy lead, not approval of any selected recording: https://www.nasa.gov/nasa-brand-center/images-and-media/ . Check third-party content and other restrictions individually.
- Library of Congress directs users to item-level rights statements: https://www.loc.gov/legal/security-copyright-and-privacy/understanding-copyright/ . Hosting alone is not permission.
- Candidate English acoustic model: https://huggingface.co/facebook/wav2vec2-base-960h . Model card lists Apache-2.0 and 16-kHz speech input. This verifies a model candidate, not downloaded weights, CPU speed or alignment quality.
- Independent transcript lead: W3C hosts the same historical excerpt plus a separate HTML transcript as ACT test material. Its repository licenses documents under the W3C Document License, but recording-specific redistribution/derivative rights remain unclear, so the audio is not approved for the public dataset. Details and checksums are in docs/REPAIRLAB_AUDIO_SMOKE.md.
- Selected calibration corpus: VCTK 0.92 is officially published under CC BY 4.0 with 110 speakers and common passages. A range-based tool fetches only declared speaker/text pairs and writes checksums plus attribution. VCTK supports alignment and acoustic validation; it is not labelled expert oratory. Source decision and private smoke hashes are in docs/REPAIRLAB_SOURCES.md.

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

Pair-pipeline increment: 42/42 tests passed. Two new integration tests exercise the Python API and actual module CLI from WAV/alignment inputs through strict JSON output. Synthetic output includes overlay series and correctly grounds a quiet word after a longer pause. No approved public-speech pair or independently validated alignment has run through this command yet.

Feature/explanation increment: 40/40 tests passed. Five new synthetic tests cover pitch/FFT/energy extraction, word aggregation, within-speaker normalization, global-gain invariance, timestamped energy/pause deviations, mismatched transcripts and invalid audio. The development threshold is uncalibrated, and no claim is made about real-speech localization or delivery quality. Equations and limits: docs/REPAIRLAB_FEATURES.md.

Dataset audit increment: 35/35 tests passed. New regressions verify that transcript/alignment changes alter clean derivative IDs, original-file hashes and rights assertions are exported without local paths, and a later invalid plan creates no partial output. Format v2 now binds derivative IDs to audio, transcript and alignment. All new checks use generated waveform fixtures and fictional rights metadata. Uploaded Track C and submission-guideline PDFs were extracted directly this session, confirming highly effective public speeches as the required final good baseline; VCTK is calibration-only.

Initial core: Python 3.12 / NumPy 2.3.5, 7/7 tests passed. Acoustic adapter: 10/10. Boundary evaluation: 14/14. VCTK source selection: 16/16. Corruptions: 22/22. Dataset writer: 27/27. Current control/generalization increment: 32/32 tests passed, adding smooth-envelope quieting, a non-clipping global-gain negative control, hidden control metadata, and declared held-out-method leakage rejection. Detector-facing records were tested not to contain corruption, control, expected-flaw, or label fields. Tests use generated fixture audio; they do not evaluate a detector or establish perceptual realism. Three official-archive VCTK clips were separately fetched, integrity-checked, decoded and aligned by the pinned model on CPU. Details: docs/REPAIRLAB_VCTK_ALIGNMENT.md. No manual word-boundary accuracy or delivery-performance result is available. `git diff --check` passed.
