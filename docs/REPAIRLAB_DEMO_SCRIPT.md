# Five-minute demo script

> Record only after the final package freeze, a fresh-clone rerun, the Windows browser-control smoke test, and the final evidence tables exist. Show the running project continuously; do not replace missing behavior with slides. Prediction-blind human boundary annotations evaluate the aligner; they are not training data.

## 0:00–0:30 — problem and boundary

Show the dashboard landing page. Say: “RepairLab turns vague speaking feedback into reviewable word-level evidence by comparing two recordings of the same transcript. It is not therapy, diagnosis or an accent score.”

## 0:30–1:10 — inputs and alignment

Upload an approved reference recording and one held-out participant/derivative recording plus their transcript/alignment inputs. Show that the transcript matches. Briefly state the source rights and why the reference is considered effective. Do not use VCTK as the claimed effective reference.

## 1:10–2:10 — evidence overlay

Run analysis. Switch between energy, pitch, spectral centroid and zero-crossing overlays. Point out the shared seconds axis. Select one flagged word, play its participant region, and read its numerical explanation without translating it into a medical or moral judgment.

## 2:10–2:50 — uncertainty and failure

Show a poor or ambiguous example that returns misleading/uncertain evidence. Explain alignment dependence, short-sample normalization and pitch errors. A visible failure is required for credibility.

## 2:50–3:40 — data integrity

Show the detector manifest and evaluation truth as separate files. Explain source-level speaker/text partitioning, exact synthetic timestamps, severity levels, harmless controls and the unseen corruption method. Do not expose local paths or personal recordings publicly.

## 3:40–4:30 — evaluation

Show the frozen report: alignment error, held-out region metrics, confusion matrix, control false positives, naive baselines and feature ablations. Clearly label synthetic versus real-speech results. Mention that threshold selection used development data only.

If independent human boundary measurements or frozen held-out results are still missing, do not record this section as though they exist. Show the corresponding checklist item as incomplete, describe only the verified software behavior, and do not claim alignment precision or detector accuracy.

## 4:30–5:00 — close

Summarize the contribution: transparent localization, causal numerical evidence and an auditable evaluation contract. End with limitations and the public repository/dataset link.

## Recording checks

- The four-step Windows annotation-control test passed in Chrome or Edge; record the browser/version and result.
- Two independent, prediction-blind boundary files were audited and adjudicated before quoting alignment error.
- The held-out evaluation command was rerun after the final dataset freeze; report its exact commit and manifest hashes.
- The final package was reproduced from a fresh clone after the last code/data change.
- English narration or accurate English subtitles.
- Duration between 3 and 10 minutes.
- Repository and dataset links visible and public.
- No private credentials, personal data or unlicensed audio.
- Video visibility set as required by the submission guidelines, not private.
