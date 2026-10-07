# Manual word-boundary protocol

This protocol creates an independent timing reference for the real-audio gate. Model output, forced-alignment output and injection metadata must not be used to choose the reference boundaries.

1. Verify the recording checksum and independently checked transcript.
2. In an audio editor, listen at normal speed, then inspect the waveform/spectrogram. Mark the audible onset and offset for a predeclared word sample spanning the beginning, middle and end of the clip. Do not move a label after viewing the model prediction.
3. Record ambiguous cases and the annotation tool/version. Use `evidence_type: human_manual`, the recording SHA256, an ISO-8601 `annotated_at` value and one entry per word:

```json
{
  "evidence_type": "human_manual",
  "audio_sha256": "full SHA256",
  "annotation_method": "Auditory review plus waveform inspection in TOOL VERSION; model timestamps hidden",
  "annotated_at": "2026-10-07T00:00:00Z",
  "words": [
    {"word_index": 0, "word": "WE", "start_seconds": 0.0, "end_seconds": 0.0}
  ]
}
```

Replace the zero placeholders with valid measured boundaries. Run:

```sh
python -m repairlab.evaluate_alignment alignment.json manual-boundaries.json
```

Report labelled-word coverage, start/end MAE, boundary median/p95/max absolute error and the fraction within 100 ms. Do not generalize one clip's result to other speakers, acoustic conditions or the later delivery detector. A second annotator or adjudication is preferred for ambiguous boundaries; report it separately rather than averaging labels silently.
