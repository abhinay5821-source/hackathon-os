# Contrastive corruption foundation

`repairlab.corruptions` creates three deterministic, transcript-preserving synthetic flaw families with exact output-sample and output-time labels:

| Family | Mild | Medium | Severe | Duration effect |
|---|---:|---:|---:|---|
| Quiet region | −6 dB | −12 dB | −20 dB | unchanged |
| Inserted pause | 0.20 s | 0.45 s | 0.80 s | increases |
| Rushed region | 1.15× | 1.35× | 1.65× | decreases |

Generator labels have provenance `synthetic_generator_truth_not_detector_input`. Store them outside detector inputs and use them only for evaluation. Every derivative inherits its source recording's speaker/text split; derivatives of one source must never cross partitions.

The current rushed baseline uses deterministic linear resampling and therefore changes pitch. It is useful for pipeline testing but cannot be the only rush method: a pitch-preserving alternate corruption must be held out to test whether the detector learned rushed delivery rather than resampling artifacts. Likewise, quiet and pause transforms are scripted flaws, not proof that the detector generalizes to human delivery mistakes.

Still required before readiness milestone 2: a dataset writer with immutable source/derivative IDs, silence-safe region selection based on validated word boundaries, flat-pitch corruption, harmless gain/pitch controls, source-partition enforcement, at least one unseen corruption method, and execution on the licensed corpus. No generated audio is committed yet.
