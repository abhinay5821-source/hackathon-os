# Michelle Obama museum-address alignment precheck — 2026-10-08

This adds a third distinct public-speaker/text candidate. It is a real-speech execution and transcript audit, not human timing validation.

## Recording-specific source evidence

- Archived White House item: https://obamawhitehouse.archives.gov/photos-and-video/video/2014/05/08/first-lady-speaks-museum-and-library-services-national-medal-award
- Direct MP3: https://obamawhitehouse.archives.gov/videos/2014/May/050814_FLOTUS.mp3
- The item says `May 08, 2014 | 20:04 | Public Domain`, links the MP3 and embeds the event transcript.
- Retrieved MP3: 19,298,471 bytes; duration 1,204.584378 seconds; SHA256 `4cdecf34571686b009e95f2041133df89b178c1569527b35ecaae35c2bf55541`.

## Baseline-suitability hypothesis

The selected passage is a formal White House address challenging museums and libraries to reach underserved children. It contains a repeated transition (“I want to challenge you”) and a three-part parallel list (“the kids who…”). These predeclared structures permit timing, pause and emphasis comparisons without declaring one overall speaking style universally correct. This is a textual/acoustic rationale, not listener-outcome evidence.

## Transcript audit and execution

- Excerpt window: 294.30–322.95 seconds of the archive MP3.
- Decoded WAV: mono 16-bit PCM, 16 kHz, 28.650 seconds; SHA256 `8972cb921c4a0e32bcc85b6c68fd29d1a189fae79cdfe36025e08d503a0dcdc7`.
- Transcript: 75 normalized words from the official passage beginning “So I want to applaud you” and ending “positive learning environments.”
- Independent Tiny English Whisper locator: 75 words; all 75 matched the official normalized sequence. This is a transcript cross-check, not timing ground truth.
- Forced aligner: `facebook/wav2vec2-base-960h`, CPU, 2.471 seconds including local model load; 75 word spans emitted.

Across the 150 matched starts/ends, Wav2Vec2-vs-Whisper absolute disagreement was: median 0.1018 seconds, p95 0.4506 seconds, maximum 0.9958 seconds and 0.5000 within 100 ms. These are two-model disagreement figures only. Their long tail reinforces the need for blind auditory/waveform annotations.

## Corpus decision

Kennedy, Barack Obama and Michelle Obama now provide three distinct speakers and texts with recording-specific public-domain evidence and successful CPU forced-alignment execution. They can support a provisional source-level train/development/test layout, but one excerpt per partition is not a credible performance evaluation. The split must be frozen only after additional eligible excerpts and human timing labels exist. Audio and model weights remain private and uncommitted.

A Biden recording was also screened because its item is public domain, but its page labels the transcript “As Prepared for Delivery” and the recording contains delivery deviations. It remains excluded unless a separately checked delivered transcript is produced.
