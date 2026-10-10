# Threshold calibration

Select the detector threshold only on development clips, then lock it for held-out scoring:

```bash
python -m repairlab.calibrate_threshold \
  pairs.jsonl evaluation_truth.jsonl detector_manifest.jsonl \
  --candidates 1.5 2.0 2.5 3.0 --output calibration-report.json
```

The manifests must share the same derivative IDs and contain nonempty `development` and `held_out` partitions. Selection maximizes development-region F1, then prefers lower control false-positive rate, then the higher threshold. Held-out truth is accessed only after selection and cannot influence the chosen value.

This prevents direct test-set tuning, but it does not make a small or synthetic development set representative. The threshold is valid only for the frozen features, alignment pipeline and evaluated data. Real-speech calibration and independent timing labels remain required.
