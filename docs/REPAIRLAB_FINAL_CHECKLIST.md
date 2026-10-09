# Final submission checklist

Status meanings: **done** = evidence exists; **blocked** = external/manual evidence required; **open** = authorized engineering/documentation work remains.

| Requirement | Status | Evidence or next action |
|---|---|---|
| CPU forced alignment implementation | done | `repairlab/audio_align.py`, acoustic adapter and tests |
| Approved effective-public-speaker references | blocked | Recording-specific rights, derivative permission and suitability rationale required |
| Independent human word-boundary error | blocked | Prediction-blind package/UI exists; validate controls, obtain two independent annotations, adjudicate disagreements, then run `repairlab.evaluate_alignment` |
| Contrastive severity-gradient data | open | Builder exists; freeze plan after approved sources |
| Harmless pitch control | done in contract | Duration-preserving synthetic vibrato; final false-positive result pending |
| Flat-pitch flaw | done in contract | Duration-preserving regional generator with mild/medium/severe levels; listener-naturalness and held-out results pending |
| Source/speaker/text holdouts | done in contract | Must be demonstrated on final dataset |
| Timestamped feature explanations | done in prototype | Threshold and delivery meaning remain unvalidated |
| Upload dashboard and overlays | done in prototype | HTTP tests exist; manual browser/judge-usability pass required |
| Held-out detector evaluation | open | Evaluator, baselines, calibration and ablations exist; final dataset/results absent |
| Public source and dataset link | blocked | Cannot publish until source rights pass |
| Fresh-clone core reproduction | done for current head | New clone and venv at `bb2e6d9`, pinned NumPy, 81/81 tests; rerun after package freeze |
| Technical document, maximum 6 pages | open | Draft exists; render, measure and replace all `PENDING` fields |
| Running-project video, 3–10 minutes | blocked | Human recording/upload required after final build |
| Devpost registration/team/terms | blocked | Human-controlled action only |
| Final submission | blocked | Human-controlled action only |

Do not describe the entry as submission-ready while any required row remains blocked or open.
