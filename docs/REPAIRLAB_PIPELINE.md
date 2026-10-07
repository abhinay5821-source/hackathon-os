# Runnable pair-analysis pipeline

Once baseline and participant recordings have independently generated forced-alignment JSON, the current CPU pipeline runs with:

```sh
python -m repairlab.analyze baseline.wav participant.wav baseline-alignment.json participant-alignment.json --output analysis.json
```

Both WAV files must be mono 16-bit PCM at 16 kHz and no longer than 60 seconds. Each alignment JSON must contain a `words` array with matching word strings plus numeric `start_seconds` and `end_seconds` fields. The output is strict JSON with:

- baseline and participant frame series for energy, F0, spectral centroid and zero-crossing rate;
- baseline and participant aligned-word summaries, including durations and preceding pauses;
- speaker-normalization parameters;
- participant timestamps and mathematical explanations for regions above the development threshold;
- explicit uncertainty notes.

This file is designed as the processing contract for the future dashboard. The command does not run forced alignment itself and does not accept an unaligned transcript. Its alignment inputs must come from the pinned acoustic pipeline and still require independent timing validation. Its threshold is not calibrated, and its output is not a validated delivery score.
