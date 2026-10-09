"""Align short 16-kHz mono PCM speech using a locally cached Wav2Vec2 model.

Model download is a separate setup action. Runtime never contacts model hosting.
"""
import argparse
import hashlib
import json
import re
import time
import wave
from pathlib import Path

import numpy as np

from repairlab.align import align


def load_audio(path):
    with wave.open(str(path), "rb") as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
            raise ValueError("Require mono 16-bit PCM WAV at 16000 Hz")
        if not 0 < audio.getnframes() <= 60 * 16000:
            raise ValueError("Require a nonempty excerpt no longer than 60 seconds")
        count = audio.getnframes()
        raw = audio.readframes(count)
    if len(raw) != count * 2:
        raise ValueError("Truncated WAV")
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0


def normalize_transcript(text):
    if not text.isascii():
        raise ValueError("Initial model supports ASCII English transcripts only")
    # Explicit normalization: punctuation is removed, whitespace is collapsed.
    normalized = re.sub(r"[^A-Z' ]", " ", text.upper())
    normalized = " ".join(normalized.split())
    if not normalized or any(char.isdigit() for char in text):
        raise ValueError("Supply written-out words, not numerals or empty text")
    return normalized


def align_audio(audio_path, transcript, model_path):
    import torch
    from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

    samples = load_audio(audio_path)
    text = normalize_transcript(transcript)
    started = time.perf_counter()
    processor = Wav2Vec2Processor.from_pretrained(str(model_path), local_files_only=True)
    model = Wav2Vec2ForCTC.from_pretrained(str(model_path), local_files_only=True, use_safetensors=True).cpu().eval()
    ids = processor.tokenizer(text, add_special_tokens=False).input_ids
    if processor.tokenizer.unk_token_id in ids:
        raise ValueError("Transcript contains unsupported acoustic-model tokens")
    inputs = processor(samples, sampling_rate=16000, return_tensors="pt")
    with torch.inference_mode():
        logits = model(**inputs).logits[0]
        probabilities = logits.log_softmax(-1).cpu().numpy()
    duration = len(samples) / 16000
    result = align(probabilities, ids, duration, processor.tokenizer.pad_token_id)
    words = []
    current = []
    separator = processor.tokenizer.word_delimiter_token_id
    for token in result["tokens"]:
        if token["token_id"] == separator:
            if current:
                words.append(current); current = []
        else:
            current.append(token)
    if current:
        words.append(current)
    text_words = text.split()
    if len(words) != len(text_words):
        raise ValueError("Word grouping did not match normalized transcript")
    result.update({"normalized_transcript": text,
                   "words": [{"word": word, "start_seconds": spans[0]["start_seconds"],
                              "end_seconds": spans[-1]["end_seconds"]} for word, spans in zip(text_words, words)],
                   "duration_seconds": duration,
                   "audio_sha256": hashlib.sha256(audio_path.read_bytes()).hexdigest(),
                   "elapsed_seconds_including_model_load": round(time.perf_counter() - started, 3),
                   "device": "cpu", "model_path": str(model_path),
                   "claim": "Real-audio inference when run; word timing accuracy remains unvalidated until manual scoring."})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = align_audio(args.audio, args.transcript.read_text(), args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    print(json.dumps({"words": len(result["words"]), "duration_seconds": result["duration_seconds"],
                      "elapsed_seconds": result["elapsed_seconds_including_model_load"], "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
