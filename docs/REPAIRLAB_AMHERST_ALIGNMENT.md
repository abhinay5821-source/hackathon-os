# Amherst real-speech alignment precheck — 2026-10-08

This is a reproducible precheck on one recording-specific public-domain candidate. It is **not** the required human timing validation and does not pass readiness milestone 1.

## Source and excerpt

- JFK Library item: https://www.jfklibrary.org/asset-viewer/archives/jfkwha-234-003 (item says `Copyright Status: Public Domain`).
- Official transcript: https://www.arts.gov/about/kennedy-transcript .
- Full MP3 SHA256: `e1a8563994e6dc25a1d863f0dd12c2bcdfe5abb3d57720666823059d1e848461`.
- Excerpt: 494.80–524.50 seconds of the archive MP3, decoded to mono 16-bit PCM at 16 kHz; duration 29.700 seconds; WAV SHA256 `857227d8048d94f2ff96967dbfcd3ac7f845c8eeee83b3ac2ced45aee9b5a207`.
- Transcript: the 55-word prose passage beginning “Our national strength matters” and ending “easy consolation.” The following quoted poem was deliberately excluded.

The excerpt start/end were located with an independent Tiny English Whisper transcript and then checked against the official NEA words. The locator transcript split `unsparing` into two words but otherwise matched 54 of the 55 normalized official words. This transcript locator is not ground truth.

## Forced-alignment execution

`facebook/wav2vec2-base-960h` ran on CPU through `repairlab.audio_align` and produced 55 word spans in 2.580 seconds including local model load. The model snapshot was freshly fetched; Transformers warned that `wav2vec2.masked_spec_embed` was newly initialized, as recorded in prior smoke runs. Audio and model files remain private and are not committed.

For a non-authoritative sanity check, matching Wav2Vec2 forced-alignment spans were compared with Tiny Whisper word timestamps. Of 55 official words, 54 matched the locator token sequence. Across the 108 matched starts/ends:

- median absolute disagreement: 0.0915 seconds;
- approximate p95 absolute disagreement: 0.7081 seconds;
- maximum absolute disagreement: 1.1549 seconds;
- fraction within 100 ms: 0.5463.

These are **two-model disagreement** numbers, not alignment errors. The long tail is large enough that the alignment must not be presented as precise. Tiny Whisper timestamps can themselves be wrong, and automatic agreement would not replace blind auditory labels.

## Gate decision

The real-audio inference path passes an execution check on a transcript-matched effective-speech candidate. The accuracy gate remains open. A human must mark a predeclared spread of word onsets/offsets with model timestamps hidden, following `docs/ALIGNMENT_ANNOTATION.md`; only `repairlab.evaluate_alignment` against that record may produce the reported boundary-error result. More independently justified speakers are also required for source-level holdouts.
