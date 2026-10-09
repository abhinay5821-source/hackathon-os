# Final submission checklist

Status meanings: **done** = evidence exists; **blocked** = external/manual evidence required; **open** = authorized engineering/documentation work remains.

| Requirement | Status | Evidence or next action |
|---|---|---|
| CPU forced alignment implementation | done | `repairlab/audio_align.py`, acoustic adapter and tests |
| Approved effective-public-speaker references | blocked | Recording-specific rights, derivative permission and suitability rationale required |
| Windows annotation controls | blocked | In Chrome or Edge, record browser/version and pass audio playback, 3-second zoom, +20 ms seek and visible-section replay; a pass proves UI function only |
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

## Required release order

1. Pass and record the Windows annotation-control check.
2. Collect two independent prediction-blind boundary files and adjudicate flagged disagreements.
3. Approve source rights and freeze the source-disjoint dataset manifest.
4. Run held-out alignment/detector evaluation, controls, baselines, ablations and failures from the frozen manifest.
5. Replace every `PENDING` field, render the technical document at no more than six pages, and rerun from a fresh clone.
6. Record the running-project video only after steps 1–5 pass.
7. Leave registration, terms acceptance, account publication and final submission to the human owner.

If a step fails, keep later dependent steps blocked. Never substitute synthetic tests, two-model disagreement, or browser functionality for independent human boundary-error evidence.
