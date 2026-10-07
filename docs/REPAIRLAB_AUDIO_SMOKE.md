# Real-audio CPU smoke test — 2026-10-07

## Actual execution

Downloaded NASA's 28-second Kennedy/Rice excerpt privately, decoded it with ffmpeg to mono 16-bit PCM 16000-Hz WAV, loaded Wav2Vec2 safetensors on CPU, ran greedy recognition and aligned that candidate transcript through the CTC core. This checks the real-audio execution path only. The model-generated transcript contains errors; it is not independent ground truth. No manual word-boundary error or delivery-accuracy result is claimed.

- Archive page: https://www.nasa.gov/history/SP-4225/multimedia/before-video.htm
- Linked recording: https://www.nasa.gov/wp-content/uploads/static/history/SP-4225/imagery/videos/v-004.mpg
- Source MPEG: 2,142,212 bytes; SHA256 `95b594e413dd2569146317fe043f6eb712258873ec615326142be65b1823c2b1`.
- Decoded WAV SHA256: `de21a3413b2152d23fb52f2ee2f4e2204d5a71aaebde2df243b7c0a489c93872`.
- Actual duration: 28.290625 seconds.
- Model: `facebook/wav2vec2-base-960h`, snapshot `22aad52d435eb6dbaf354bdad9b0da84ce7d6156`.
- Python 3.12; PyTorch 2.14.1+cpu; Transformers 4.57.1; NumPy 2.5.3; torch threads=2.
- Recognition inference: 3.121 seconds excluding model load/download, one local measurement.
- Alignment adapter: 3.859 seconds including model load and acoustic inference, one local measurement; 66 words in the ASR candidate.
- Model-loading warning: `wav2vec2.masked_spec_embed` was newly initialized. Model was run in eval/inference mode; no training or timing accuracy claim follows from this smoke test.

Raw recording, generated transcript and alignment JSON are not committed. The recording is a candidate for educational experiments, not an approved public derivative dataset. The measured runtime is specific to this execution machine and short clip, not a laptop performance guarantee.

## Reuse and baseline gate remain open

NASA's https://www.nasa.gov/nasa-brand-center/images-and-media/ policy generally permits educational/informational use of its own media, but distinguishes third-party materials and commercial identifiable-person uses. AI output must not suggest NASA verification or endorsement. This clip's historical speech is a plausible rhetorical reference because it uses deliberate emphasis and pause structure, but no expert/rubric rating was obtained. Recording-specific provenance/derivative suitability and the public dataset's exact use must be documented before release. NASA archival hosting alone is not sufficient clearance. Further candidate transcript reference: https://www.nasa.gov/history/60-years-ago-president-kennedy-reaffirms-moon-landing-goal-in-rice-university-speech/ ; excerpt wording and clip boundaries still need independent listening checks.

## Reproduce the adapter

Install `repairlab-acoustic-requirements.txt` in an isolated venv. Separately download/cache the model snapshot above using Hugging Face (no login needed for this model), preserving its license. Runtime uses `local_files_only=True`; it cannot silently download a replacement model. Supply a separately checked transcript and a <=60-second mono PCM WAV:

```sh
python -m repairlab.audio_align clip.wav checked-transcript.txt --model /path/to/cached/snapshot --output alignment.json
```

The CLI exports normalized transcript, word/token spans, duration and elapsed time. The current timing approximation uniformly spreads emissions across the clip; validate model-frame timing and manually scored boundaries before treating it as precise alignment. No delivery scores or clinical conclusions are produced.

## Verification

`python -m unittest discover -s tests -v`: **10/10 tests pass**, including PCM sample preservation, wrong-rate rejection and explicit English-transcript normalization. Seven prior core/provenance tests still pass. These are unit checks, separate from the one real-audio smoke run. `git diff --check` passed.

Next: independently check transcript and word-boundary labels on multiple excerpts; record median and tail boundary errors, including poor audio and transcript mismatch. Complete recording-specific reuse review and held-out corpus design. Full readiness remains 0/6 milestones.
