# Track C fit audit — 2026-10-09

Source: uploaded Copy of Track C.pdf, three pages, read in full on 2026-10-09. This audit distinguishes requirements from internal design choices.

## Required outcome

The challenge explicitly requests reproducible custom evaluative rubric-based scores and actionable delivery feedback for competitive spoken performances. Transcript-matched good/bad audio is the required experimental design, not the entire user benefit. It controls wording while evaluating delivery. The brief requires exact flaw timestamps, human-readable mathematical rationale, uploads and baseline/participant feature overlays. Evaluation weights: data engineering/stress testing 30%; causal explainability/temporal grounding 25%; feature extraction 20%; dashboard 15%; reproducibility/code quality 10%. Mathematical rationale must link acoustic deviation to context.

## Current gaps

- Word-level acoustic deltas and candidate flaw types exist. A delta alone does not show that delivery is wrong or prescribe a justified correction.
- Development threshold 2.5 is not a validated evaluative rubric. No final, calibrated delivery score is demonstrated.
- Highly effective public-speech excerpts have CPU alignment execution evidence. Human boundary accuracy remains unmeasured; one blind human sample now exists but predictions must be recovered before comparison.
- Public source rights, the final contrastive spectrum, held-out performance, public dataset URL and final documentation/video remain incomplete.
- Two annotators are an internal reliability protocol, not a stated Track C requirement. Dataset quality is explicitly prioritized over quantity.

## Next implementation acceptance criteria

Each feedback item must expose the affected words and participant start/end, observed feature value with units, baseline value, normalized delta, and calibrated rubric component. Preserve timestamped playback and uncertainty.

For pause, pacing and local energy candidates, give an evidence-grounded rehearsal action (for example replay the marked phrase and test a shorter pause). Quantify the measured gap, not an invented optimal target. Any suggested target range must be derived from declared reference evidence and labelled as a reference range, not a universal ideal. Do not prescribe copying another speaker's absolute pitch or volume.

Distinguish acoustic evidence, contextual interpretation and suggested action in the output. If context cannot justify a delivery flaw, return acoustic deviation/needs review rather than a confident diagnosis. Do not equate spectral proxies with clarity or synthetic detection with listener benefit.

Implement and evaluate a documented rubric before describing the project as satisfying scoring. Test repeatability, controls, near-perfect/mild/severe behavior and failures on held-out sources, without tuning on held-out truth. Report synthetic performance separately from natural delivery validity.

Next task: inspect feature-to-dashboard output contracts, add the evidence/action distinction with conservative phrasing and meaningful tests, then integrate a declared rubric subject to development calibration. In parallel recover existing model predictions for the provisional single-annotator boundary evaluation. No new human desktop task is prepared or required tonight.
