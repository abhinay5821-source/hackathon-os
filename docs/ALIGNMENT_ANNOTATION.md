# Manual word-boundary protocol

This protocol creates an independent timing reference for the real-audio gate. Model output, forced-alignment output and injection metadata must not be used to choose the reference boundaries.

Create the prediction-free package before either annotator sees model output:

```sh
python -m repairlab.prepare_annotation clip.wav transcript.txt blind-package \
  --clip-id source-excerpt --sample-count 12
```

The package copies the validated 16-kHz mono WAV, normalizes the transcript, preselects words across the entire clip and emits an empty label template. It deliberately contains no alignment or prediction timestamps. Make a separate copy of the template for each annotator.

Annotators do not need to edit JSON. Start the local, dependency-free annotation screen:

```sh
python -m repairlab.annotation_ui blind-package
```

Open `http://127.0.0.1:8766`, enter a non-personal annotator ID and the audio tool/browser version, then play, seek and mark each word's audible start and end. The browser downloads a completed JSON file locally. Use a fresh annotator ID and an unmodified package for the second pass; neither annotator should see model output or the other's labels.

1. Verify the recording checksum and independently checked transcript.
2. Predeclare the word indexes, then give the same checksum, transcript and indexes to two annotators. Hide model and forced-alignment timestamps from both annotators.
3. In an audio editor, listen at normal speed, then inspect the waveform/spectrogram. Mark the audible onset and offset for the predeclared sample spanning the beginning, middle and end of the clip. Do not move a label after viewing the model prediction.
4. Record ambiguous cases and the annotation tool/version. Use non-personal annotator IDs, `prediction_hidden: true`, `evidence_type: human_manual`, the recording SHA256, an ISO-8601 `annotated_at` value and one entry per word:

```json
{
  "evidence_type": "human_manual",
  "audio_sha256": "full SHA256",
  "annotation_method": "Auditory review plus waveform inspection in TOOL VERSION; model timestamps hidden",
  "annotated_at": "2026-10-07T00:00:00Z",
  "annotator_id": "ann-a",
  "prediction_hidden": true,
  "words": [
    {"word_index": 0, "word": "WE", "start_seconds": 0.0, "end_seconds": 0.0}
  ]
}
```

Replace the zero placeholders with valid measured boundaries. Audit the two independent files before either is compared with model output:

```sh
python -m repairlab.audit_annotations annotator-a.json annotator-b.json --tolerance 0.1
```

Any queued word requires explicit review. Do not average boundaries silently. Preserve the two original files and document adjudicated changes separately. After the audit, run model scoring against the declared reference:

```sh
python -m repairlab.evaluate_alignment alignment.json manual-boundaries.json
```

Report inter-annotator disagreement and its adjudication queue separately from model error. Then report labelled-word coverage, start/end MAE, boundary median/p95/max absolute error and the fraction within 100 ms. Do not generalize one clip's result to other speakers, acoustic conditions or the later delivery detector.
