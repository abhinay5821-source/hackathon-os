# RepairLab — technical report draft

> Draft only. Replace every `PENDING` field with measured evidence before submission. Keep the rendered document at six pages or fewer.

## 1. Problem and scope

Speakers often receive vague advice such as “slow down” or “use more energy.” RepairLab is a transparent, transcript-matched comparison tool that localizes measurable delivery differences between a reference recording and a participant recording. It highlights aligned word regions and explains each flag through normalized acoustic or timing deltas.

The prototype is an analysis and review aid, not a speech-therapy system, diagnostic device, fluency judge or replacement for a teacher. It does not score identity, accent or disability.

## 2. Contribution

RepairLab combines:

1. CPU forced alignment that maps the same transcript to both recordings.
2. Word-level energy, F0, spectral-centroid, zero-crossing, duration and pause evidence.
3. Per-recording robust normalization using median/MAD with declared scale floors.
4. Timestamped mathematical explanations and uncertainty statements.
5. A contrastive dataset protocol with severity gradients, controls, exact transformed labels and source-level speaker/text holdouts.
6. Truth-isolated detection, dev-only threshold calibration, held-out scoring, uninformed baselines and feature-group ablations.

The intended novelty is the auditable experimental contract: every detected region can be traced to aligned measurements, while corruption truth and generator parameters remain inaccessible to the detector. Novelty relative to published prior art is `PENDING PRIMARY-SOURCE REVIEW`.

## 3. System

Both 16-kHz recordings are forced-aligned to a normalized shared transcript. Frame features are summarized inside word boundaries. For feature \(f\), recording \(r\), and word \(i\):

\[
z_{r,i,f}=\frac{x_{r,i,f}-\operatorname{median}(x_{r,\cdot,f})}
{\max(1.4826\operatorname{MAD}(x_{r,\cdot,f}),\epsilon_f)}
\]

The displayed difference is \(\Delta_{i,f}=z_{participant,i,f}-z_{reference,i,f}\). A word is flagged when \(|\Delta_{i,f}|\ge\tau\) for at least one enabled feature. Threshold \(\tau\) is selected on development clips only and then locked for held-out evaluation.

The local dashboard provides synchronized evidence overlays, flagged time regions, playback and uncertainty. Uploaded audio is processed through temporary files and deleted after each request; this local prototype is not a hardened public service.

## 4. Data and experimental controls

Final reference recordings must be legally reusable examples of highly effective public delivery with recording-specific rights and a written suitability rationale. `PENDING: APPROVED REFERENCES AND LICENSE TABLE`.

VCTK CC BY 4.0 clips are used only for calibration of audio ingestion and alignment; they are not presented as effective-public-speaker exemplars. Synthetic derivatives include quiet, rushed and inserted-pause severity gradients. Global gain is a harmless control. Alternate corruption methods are held out. All derivatives of one recording remain in one partition, with speaker and text identities disjoint across partitions.

Detector inputs exclude corruption type, severity, expected outcome, labels and transformation parameters. Synthetic, self-recorded and real-user evidence are reported separately.

## 5. Evaluation protocol

Required reporting:

- alignment boundary median/max absolute error against hidden human timings;
- region precision, recall and F1 at declared temporal IoU;
- mean matched IoU and boundary error;
- flaw-type confusion including missed and extra regions;
- false positives on clean/global-gain/`PENDING PITCH` controls;
- no-flaw, full-clip and seeded-random-region baselines;
- energy, pitch, spectral and timing ablations;
- unseen speaker, unseen text and alternate-method failures.

Current automated status: 60 tests validate software contracts and synthetic fixtures. `PENDING: FROZEN DATASET COUNTS, REAL ALIGNMENT ERROR, HELD-OUT DETECTOR TABLES AND FAILURE EXAMPLES.` Passing code tests is not detector-performance evidence.

## 6. Limitations, ethics and reproducibility

Forced alignment can produce plausible timestamps for an incorrect transcript. Pitch estimation can fail on unvoiced speech or octave errors. Per-speaker normalization removes absolute level and can behave poorly on short recordings. Synthetic transformations do not reproduce all natural delivery differences. A reference style is contextual rather than universally “correct.”

RepairLab must not penalize accent, neurodivergence or disability, and must not make medical or therapeutic claims. Users should control their recordings and understand the uncertainty of every flag.

Reproduction requires Python 3.12, pinned dependencies, public source/dataset links, exact manifests and seeds. `PENDING: FRESH-CLONE RESULT, PUBLIC DATASET URL, COMMIT SHA, HARDWARE AND RUNTIME TABLE.`
