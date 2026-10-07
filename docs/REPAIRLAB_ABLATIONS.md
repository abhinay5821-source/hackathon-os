# Feature ablations

Run the full detector and four leave-one-group-out variants:

```bash
python -m repairlab.ablate_detector pairs.jsonl evaluation_truth.jsonl detector_manifest.jsonl --output ablation-report.json
```

Variants remove energy, pitch, spectral (centroid plus zero-crossing rate), or timing (word duration plus preceding pause). Predictions are regenerated from audio/alignment pairs; the detector receives no truth, corruption type, severity or generator parameter.

An ablation measures detector dependence under the evaluated data. It does not prove perceptual importance, effective-delivery causality or clinical meaning. Synthetic and real-speech reports must remain separate.
