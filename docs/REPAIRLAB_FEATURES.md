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

## Claim limits

The current threshold of 2.5 is a development default, not a validated scoring rubric. Autocorrelation pitch is a transparent CPU baseline and can produce octave errors, especially for noisy, breathy or multi-pitch audio. Spectral centroid and zero-crossing rate are proxies, not direct measures of vocal clarity. Word spans inherit all forced-alignment errors. Short clips, flat feature sequences and missing pitch values reduce reliability.

Five synthetic tests verify a 200 Hz tone, the expected 6.02 dB energy increase when amplitude doubles, aligned-word aggregation, cancellation of a global gain control, and timestamped energy/pause outlier explanations. They do not establish performance on real speeches or human delivery errors.

Before readiness milestone 3, run these features on the frozen licensed contrastive dataset, tune thresholds only on development sources, freeze normalization floors, measure held-out localization/type errors, add uncertainty and ablations, and compare against naive fixed thresholds. Do not describe output as causal in a scientific sense; it is a mathematical rationale for an observed acoustic deviation.
