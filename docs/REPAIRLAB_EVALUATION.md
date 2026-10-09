# Detector evaluation

Before prediction or scoring, verify the frozen dataset byte-for-byte:

```bash
python -m repairlab.verify_dataset dataset
```

The command validates the provenance and detector/truth manifests, every declared WAV hash, and the exact WAV filename set. Any mismatch, missing file or unexpected WAV blocks evaluation. Archive the successful JSON output with the final report.

Then generate predictions from a pair manifest that contains audio and alignment paths but no evaluation labels:

```bash
python -m repairlab.batch_detect pairs.jsonl --output predictions.jsonl --threshold 2.5
```

Then score them:

```bash
python -m repairlab.evaluate_detector \
  dataset/evaluation_truth.jsonl predictions.jsonl dataset/detector_manifest.jsonl \
  --output evaluation-report.json
```

Prediction rows require the same `derivative_id` set as the isolated truth file and a `regions` array. Each region contains `start_seconds`, `end_seconds` and `candidate_flaw_type`. The evaluator never passes truth to the detector.

The transparent baseline assigns a candidate type from signed evidence: a longer preceding pause suggests `inserted_pause`, a shorter normalized word duration suggests `rushed`, and lower normalized energy suggests `quiet`. When several rules fire, the largest absolute normalized delta wins. Other deviations remain `unclassified_acoustic_deviation`. These are hypotheses for a confusion matrix, not semantic ground truth.

The report includes region precision, recall and F1 at a declared temporal-IoU threshold; mean IoU and mean boundary error for matched regions; exact flaw-type accuracy; a confusion matrix including missed and extra regions; and false-positive rate on clean/control clips. It also scores three deterministic uninformed baselines: no flaws, one full-clip region and one seeded random quarter-clip region.

Matching greedily selects the highest remaining IoU and is deterministic. It is not a globally optimal assignment. Metrics against synthetic labels measure recovery of injected regions, not perceived speech quality, listener outcomes or therapeutic benefit. Final reporting must keep synthetic, self-recorded and real-user evidence separate.

Feature-group ablations use `python -m repairlab.ablate_detector`; see `docs/REPAIRLAB_ABLATIONS.md`.

Development-only threshold selection and locked held-out scoring use `python -m repairlab.calibrate_threshold`; see `docs/REPAIRLAB_CALIBRATION.md`.

Run `python -m repairlab.verify_dataset dataset` again after evaluation. The before/after verifier output must match; otherwise discard the results and investigate the dataset mutation.

After development-only calibration, freeze the rubric and score only the held-out partition with:

```bash
python -m repairlab.freeze_rubric calibration.json --output frozen-rubric.json
python -m repairlab.score_held_out pairs.jsonl evaluation_truth.jsonl detector_manifest.jsonl frozen-rubric.json --output held-out-score.json
```

The held-out command verifies the rubric fingerprint, selects only manifest rows declared `held_out`, and persists both rubric and calibration SHA-256 values beside the detector report and baselines. It rejects a modified config or an empty held-out partition. Dataset verification before and after this command remains mandatory.
