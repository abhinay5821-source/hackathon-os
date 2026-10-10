# Batch detector

`repairlab.batch_detect` turns a declared list of transcript-matched audio/alignment pairs into the prediction JSONL consumed by the evaluator. It deliberately accepts no truth file, corruption label, severity or generator parameter.

Each line of `pairs.jsonl` contains a unique `derivative_id` and four paths relative to the manifest:

```json
{"derivative_id":"example-01","baseline_audio":"audio/base.wav","participant_audio":"audio/example-01.wav","baseline_alignment":"align/base.json","participant_alignment":"align/example-01.json"}
```

Run:

```bash
python -m repairlab.batch_detect pairs.jsonl --output predictions.jsonl --threshold 2.5
```

Rows are sorted by ID and contain only the ID, declared threshold and detected timestamped regions. Absolute paths and paths escaping the manifest directory are rejected. The command does not prove that the alignments, threshold or flaw types are accurate; those require independent annotation and held-out evaluation.
