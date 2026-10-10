# Contrastive corruption foundation

Negative controls include a non-clipping ±3 dB global gain change and a duration-preserving global pitch-vibrato warp (20 or 35 cents at 4.5 or 5.5 Hz). Both have `expected_flaw: false`; their parameters exist only in evaluation truth. The vibrato implementation is deterministic monotonic time warping, not studio-quality pitch shifting, and must be described as synthetic.

`repairlab.corruptions` creates four deterministic, transcript-preserving synthetic flaw families with exact output-sample and output-time labels:

| Family | Mild | Medium | Severe | Duration effect |
|---|---:|---:|---:|---|
| Quiet region | −6 dB | −12 dB | −20 dB | unchanged |
| Inserted pause | 0.20 s | 0.45 s | 0.80 s | increases |
| Rushed region | 1.15× | 1.35× | 1.65× | decreases |
| Flat-pitch region | 0.35 warp strength | 0.65 | 1.00 | unchanged |

Generator labels have provenance `synthetic_generator_truth_not_detector_input`. Store them outside detector inputs and use them only for evaluation. Every derivative inherits its source recording's speaker/text split; derivatives of one source must never cross partitions.

The current rushed baseline uses deterministic linear resampling and therefore changes pitch. It is useful for pipeline testing but cannot be the only rush method: a pitch-preserving alternate corruption must be held out to test whether the detector learned rushed delivery rather than resampling artifacts. Likewise, quiet and pause transforms are scripted flaws, not proof that the detector generalizes to human delivery mistakes.

The flat-pitch baseline estimates a local autocorrelation F0 track, targets its voiced-frame median and applies a severity-weighted monotonic time warp inside complete word spans. It preserves sample count and leaves audio outside the selected region byte-identical. This is a deterministic CPU approximation, not studio-quality pitch transformation: synthetic chirp tests show reduced estimated F0 spread, but speech naturalness, perceptual severity and real-audio detector behavior remain unvalidated.

`repairlab.dataset.build_dataset` now writes content-derived immutable derivative IDs, selects regions only from complete forced-alignment word spans, keeps every derivative of a recording in one partition, and rejects speaker/text/recording overlap across partitions. It places safe detector inputs in `detector_manifest.jsonl` and generator labels in a separate `evaluation_truth.jsonl`; the detector must never read the latter. It refuses nonempty output directories so old and new builds cannot be silently mixed.

The dataset builder also supports two quiet-generation methods: hard attenuation and a distinct cosine envelope. A plan can mark a method `holdout_method: true`; the builder then requires it to occur only in the held-out partition and rejects leakage elsewhere. A ±3 dB whole-clip gain transform is available as a negative control with `expected_flaw: false`; positive gain refuses clipping instead of silently distorting the waveform. Control identity and parameters remain evaluation-only.

Still required before readiness milestone 2: perceptual review of flat-pitch output, approved effective-delivery sources, measured alignment error, and execution of a frozen dataset build on the licensed corpus. The vibrato control and smooth quiet method are pipeline generalization checks, not evidence of human-error realism. No generated audio is committed yet.

Format v2 additionally includes the original WAV-file checksum, normalized transcript and supplied word spans in each derivative identity. `source_provenance.json` exports attribution/rights-review metadata and alignment inputs without local paths, and `build.json` hashes it. The builder validates and renders every plan before writing any output, preventing invalid-plan partial builds. Filesystem I/O failures are still possible during publication and are not claimed atomic. Exported rights fields remain reviewer assertions, and supplied alignment spans remain unvalidated until independent boundary scoring.
