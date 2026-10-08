"""Create a prediction-free package for blind human word-boundary annotation."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from repairlab.audio_align import load_audio, normalize_transcript


def _indexes(word_count, sample_count):
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 3:
        raise ValueError("sample_count must be an integer of at least 3")
    if sample_count > word_count:
        raise ValueError("sample_count cannot exceed transcript word count")
    if sample_count == 1:
        return [0]
    return [round(i * (word_count - 1) / (sample_count - 1)) for i in range(sample_count)]


def prepare_package(audio_path, transcript, output_dir, clip_id, sample_count=12):
    """Write audio, prompts and an empty label template with no model output."""
    audio_path, output = Path(audio_path), Path(output_dir)
    if output.exists():
        raise ValueError("Output directory already exists")
    if not isinstance(clip_id, str) or not clip_id.strip() or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in clip_id):
        raise ValueError("clip_id must use only letters, digits, hyphen or underscore")
    samples = load_audio(audio_path)
    normalized = normalize_transcript(transcript)
    words = normalized.split()
    indexes = _indexes(len(words), sample_count)
    digest = hashlib.sha256(audio_path.read_bytes()).hexdigest()

    output.mkdir(parents=False)
    shutil.copyfile(audio_path, output / "audio.wav")
    (output / "transcript.txt").write_text(normalized + "\n")
    prompts = [{"word_index": index, "word": words[index]} for index in indexes]
    manifest = {
        "format": "repairlab-blind-annotation-v1",
        "clip_id": clip_id,
        "audio_sha256": digest,
        "duration_seconds": len(samples) / 16000,
        "transcript_word_count": len(words),
        "selected_words": prompts,
        "prediction_included": False,
        "instructions": "Annotate audible word onset/offset with model predictions hidden; do not change selected indexes.",
    }
    template = {
        "evidence_type": "human_manual",
        "audio_sha256": digest,
        "annotation_method": "",
        "annotated_at": "",
        "annotator_id": "",
        "prediction_hidden": True,
        "words": [{**item, "start_seconds": None, "end_seconds": None} for item in prompts],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (output / "labels-template.json").write_text(json.dumps(template, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("transcript", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--clip-id", required=True)
    parser.add_argument("--sample-count", type=int, default=12)
    args = parser.parse_args()
    result = prepare_package(args.audio, args.transcript.read_text(), args.output,
                             args.clip_id, args.sample_count)
    print(json.dumps({"output": str(args.output), "clip_id": result["clip_id"],
                      "selected_words": len(result["selected_words"]),
                      "audio_sha256": result["audio_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
