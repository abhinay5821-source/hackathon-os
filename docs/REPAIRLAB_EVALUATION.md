# Detector evaluation

Run:

```bash
python -m repairlab.evaluate_detector \
  dataset/evaluation_truth.jsonl predictions.jsonl dataset/detector_manifest.jsonl \
  --output evaluation-report.json
```

Prediction rows require the same `derivative_id` set as the isolated truth file and a `regions` array. Each region contains `start_seconds`, `end_seconds` and `candidate_flaw_type`. The evaluator never passes truth to the detector.

The transparent baseline assigns a candidate type from signed evidence: a longer preceding pause suggests `inserted_pause`, a shorter normalized word duration suggests `rushed`, and lower normalized energy suggests `quiet`. When several rules fire, the largest absolute normalized delta wins. Other deviations remain `unclassified_acoustic_deviation`. These are hypotheses for a confusion matrix, not semantic ground truth.

The report includes region precision, recall and F1 at a declared temporal-IoU threshold; mean IoU and mean boundary error for matched regions; exact flaw-type accuracy; a confusion matrix including missed and extra regions; and false-positive rate on clean/control clips. It also scores three deterministic uninformed baselines: no flaws, one full-clip region and one seeded random quarter-clip region.

Matching greedily selects the highest remaining IoU and is deterministic. It is not a globally optimal assignment. Metrics against synthetic labels measure recovery of injected regions, not perceived speech quality, listener outcomes or therapeutic benefit. Final reporting must keep synthetic, self-recorded and real-user evidence separate.
