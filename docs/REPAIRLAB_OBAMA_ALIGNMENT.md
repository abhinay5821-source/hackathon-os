# Obama Lincoln Hall alignment precheck — 2026-10-08

This is a reproducible real-speech precheck for a second speaker. It is **not** human timing validation and does not pass readiness milestone 1.

## Recording-specific source evidence

- Archived White House item: https://obamawhitehouse.archives.gov/photos-and-video/video/president-obama-speaks-dedication-abraham-lincoln-hall
- Direct MP3: https://obamawhitehouse.archives.gov/videos/2009/March/031209_WashingtonDC.mp3
- The item itself says `March 12, 2009 | 12:00 | Public Domain`, links the MP3, and embeds the White House transcript.
- Retrieved MP3: 11,695,303 bytes; duration 717.005438 seconds; SHA256 `b8a98e24d5196cbc7e0a3d8deace823c18bebadc1396879114953a9542e565fc`.

The archive metadata resolves recording-level provenance more strongly than a site-wide inference. This remains a project research determination, not legal advice about every jurisdiction.

## Baseline-suitability hypothesis

The selected passage is formal prepared public delivery at the National Defense University. It contains three matched contrastive clauses (“No technology… No army… No weapon…”) followed by an explicit transition from threat to action. That structure provides predeclared, transcript-grounded opportunities to measure timing, pause and emphasis without declaring every stylistic difference an error. Historical prominence or speaker identity alone is not used as the rationale. Listener evidence remains absent.

## Excerpt and execution

- Excerpt window: 344.20–398.10 seconds of the archive MP3.
- Decoded WAV: mono 16-bit PCM, 16 kHz, 53.900 seconds; SHA256 `403c9d1b7a5b364dc901f91c9e5434b7bf1e7b1ac2ef10342f0cbd19ea449a4d`.
- Transcript: 143 normalized words from the official paragraph beginning “We also know that the old approaches” and ending “the work that we must do.”
- Forced aligner: `facebook/wav2vec2-base-960h`, CPU, 7.596 seconds including local model load; 143 word spans emitted.

An independent Tiny English Whisper pass was used first to locate the official passage, not as ground truth. It matched 141 of 143 normalized words. Across the 282 matched starts/ends, Wav2Vec2-vs-Whisper absolute disagreement was: median 0.0817 seconds, p95 0.2988 seconds, maximum 0.6035 seconds, and 0.6277 within 100 ms.

These are **two-model disagreement** values. They neither establish which model is correct nor replace blind auditory/waveform annotations. The long tail is still too large for an unqualified precision claim.

## Gate decision

There are now two recording-specific public-domain, transcript-matched speaker candidates (Kennedy and Obama) with successful CPU forced-alignment execution. Source diversity has improved, but strict speaker/text holdouts and human word-boundary errors still require additional material and independent annotations. No audio or model weights are committed.

## Prediction/reference binding

The aligner now records the SHA-256 of the WAV bytes in every prediction. The boundary evaluator requires that hash and the declared duration to match the blind human reference before it will score any timestamps. This is an integrity gate, not new accuracy evidence.

One 15-word prediction-blind manual annotation exists for the excerpt above. The exact corresponding Wav2Vec2 prediction artifact is not present in the current execution environment, and its local acoustic-model runtime is unavailable there. Therefore no single-annotator boundary-error result is reported yet; it must be regenerated from the checksum-matched WAV rather than reconstructed or inferred.
