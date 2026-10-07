# Contrastive corruption foundation

`repairlab.corruptions` creates three deterministic, transcript-preserving synthetic flaw families with exact output-sample and output-time labels:

| Family | Mild | Medium | Severe | Duration effect |
|---|---:|---:|---:|---|
| Quiet region | −6 dB | −12 dB | −20 dB | unchanged |
| Inserted pause | 0.20 s | 0.45 s | 0.80 s | increases |
| Rushed region | 1.15× | 1.35× | 1.65× | decreases |

Generator labels have provenance `synthetic_generator_truth_not_detector_input`. Store them outside detector inputs and use them only for evaluation. Every derivative inherits its source recording's speaker/text split; derivatives of one source must never cross partitions.

The current rushed baseline uses deterministic linear resampling and therefore changes pitch. It is useful for pipeline testing but cannot be the only rush method: a pitch-preserving alternate corruption must be held out to test whether the detector learned rushed delivery rather than resampling artifacts. Likewise, quiet and pause transforms are scripted flaws, not proof that the detector generalizes to human delivery mistakes.

`repairlab.dataset.build_dataset` now writes content-derived immutable derivative IDs, selects regions only from complete forced-alignment word spans, keeps every derivative of a recording in one partition, and rejects speaker/text/recording overlap across partitions. It places safe detector inputs in `detector_manifest.jsonl` and generator labels in a separate `evaluation_truth.jsonl`; the detector must never read the latter. It refuses nonempty output directories so old and new builds cannot be silently mixed.

Still required before readiness milestone 2: flat-pitch corruption, harmless gain/pitch controls, at least one unseen corruption method, approved effective-delivery sources, measured alignment error, and execution of a frozen dataset build on the licensed corpus. No generated audio is committed yet.
