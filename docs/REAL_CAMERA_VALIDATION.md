# Real-camera validation protocol

Status: protocol and scoring harness implemented; no real-camera footage collected or evaluated.

Use a fixed, consented camera aimed only at the configured route. Avoid faces, identifying signs and private areas. Record separate sessions for clear route, persistent physical obstruction, transient passage, shadows/reflections, lighting changes, camera vibration and partial/global occlusion. Do not tune thresholds on held-out sessions.

Each case receives a human ground-truth label of `obstruction` or `clear`, a non-identifying session ID and the analyzer result JSON path. Keep development and held-out session IDs disjoint. Example:

```json
{"dataset_kind":"real_camera","held_out":true,"cases":[{"case_id":"heldout-001","session_id":"session-a","expected":"obstruction","result":"results/heldout-001.json"}]}
```

Run `python -m clearroute.evaluate manifest.json --output evaluation-report.json`. The report measures obstruction recall, false-alert rate, uncertainty rate and determinate coverage. An uncertain result is an abstention and is not silently counted as correct.

Minimum internal gate: three separately recorded held-out sessions, 30 total clips, 10 physical obstructions and 10 clear/transient cases, with every failure retained. This is a feasibility gate, not statistical or production validation.

Raw footage and personal data must not be committed publicly. Publish only non-identifying aggregate metrics and carefully selected consented demo footage.
