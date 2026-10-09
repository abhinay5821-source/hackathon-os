# Acoustic feature and explanation baseline

`repairlab.features` is a deterministic NumPy baseline for Track C feature extraction and timestamped explanations. It currently computes 25 ms frames at a 10 ms hop:

- energy: `10 log10(mean(x²) + 1e-12)` dB;
- F0: the strongest normalized autocorrelation lag from 70–400 Hz, emitted only when correlation is at least 0.30 and frame energy is at least −55 dB;
- spectral centroid: `sum(frequency * magnitude) / sum(magnitude)` from the Hann-windowed FFT;
- zero-crossing rate: the fraction of adjacent samples whose signs differ.

Frames whose centers fall inside a forced-alignment word interval are summarized by their median. Word duration and the preceding pause are added as timing features. Comparison requires matching word sequences with at least three words.

For each feature and each recording independently, values are normalized as:

`z = (value - median(recording)) / max(1.4826 * MAD(recording), feature_floor)`

The participant delta for a word is `z_participant - z_baseline`. A region is returned when the absolute delta reaches the configured threshold; output includes participant timestamps, exact deltas, normalization parameters and a templated mathematical explanation. Independent per-recording normalization makes a constant whole-recording gain shift cancel in the tested baseline.

Each returned region now separates four things: measured evidence (raw baseline and participant values, units, normalized delta and threshold), a conservative interpretation, a suggested rehearsal action, and the action's evidentiary basis. Pause, duration and local-energy candidates can produce quantified reference-based actions. Other acoustic deviations explicitly abstain from prescribing a correction. Suggested amounts describe the measured gap to this reference performance; they are not universal delivery targets.

## Development scoring rubric

The pair result includes a deterministic 0–100 development rubric. Its declared component weights are timing 0.35, energy 0.25, pitch 0.25 and spectral 0.15. For each finite word-feature delta `d`, threshold `t`, and severity cap `c=2`:

`p = min(max(abs(d) - t, 0) / (c * t), 1)`

Each component is `100 * (1 - mean(p))`. The overall score is the weighted mean of available components; feature-subset ablations renormalize over available weights. The JSON records the formula, threshold, weights, finite-measurement counts and status `development_default_uncalibrated`.

This score is a reproducible engineering rubric, not a validated judge score. The threshold must be selected on development sources only using `repairlab.calibrate_threshold`, then locked before held-out scoring. Weights and severity cap must also be frozen before held-out execution. Do not tune them using held-out labels or describe 100 as perfect human delivery.

Freeze the selected threshold and rubric constants with:

```sh
python -m repairlab.freeze_rubric calibration.json --output frozen-rubric.json
```

The output binds the complete calibration report by SHA-256 and fingerprints the canonical configuration. `verify_rubric_config` rejects any later modification. This prevents silent post-hoc tuning, but does not by itself prove the calibration data, weights or scoring construct are valid.

## Claim limits

The current threshold of 2.5 is a development default, not a validated scoring rubric. Autocorrelation pitch is a transparent CPU baseline and can produce octave errors, especially for noisy, breathy or multi-pitch audio. Spectral centroid and zero-crossing rate are proxies, not direct measures of vocal clarity. Word spans inherit all forced-alignment errors. Short clips, flat feature sequences and missing pitch values reduce reliability.

Five synthetic tests verify a 200 Hz tone, the expected 6.02 dB energy increase when amplitude doubles, aligned-word aggregation, cancellation of a global gain control, and timestamped energy/pause outlier explanations. They do not establish performance on real speeches or human delivery errors.

Before readiness milestone 3, run these features on the frozen licensed contrastive dataset, tune thresholds only on development sources, freeze normalization floors, measure held-out localization/type errors, add uncertainty and ablations, and compare against naive fixed thresholds. Do not describe output as causal in a scientific sense; it is a mathematical rationale for an observed acoustic deviation.
