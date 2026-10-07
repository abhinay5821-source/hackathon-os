"""Write reproducible clean/flawed datasets without leaking generator truth.

Detector-facing records and evaluation truth are deliberately separate files.
All derivatives from a recording must stay in one source-level partition.
"""
import hashlib
import json
import wave
from pathlib import Path

import numpy as np

from repairlab.audio_align import load_audio, normalize_transcript
from repairlab.corruptions import (global_gain_control, insert_pause, quiet_region,
                                   rush_region, smooth_quiet_region)
from repairlab.provenance import validate_source


FORMAT_VERSION = "repairlab-contrastive-v2"
ALLOWED_PARTITIONS = {"train", "development", "held_out"}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_words(words, transcript, duration):
    if not isinstance(words, list) or not words:
        raise ValueError("Require forced-alignment word spans")
    previous = 0.0
    normalized = normalize_transcript(transcript).split()
    if len(words) != len(normalized):
        raise ValueError("Word spans must match normalized transcript")
    for expected, item in zip(normalized, words):
        if item.get("word") != expected:
            raise ValueError("Word span text must match normalized transcript")
        start, end = item.get("start_seconds"), item.get("end_seconds")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            raise ValueError("Word boundaries must be numeric")
        if not previous <= start < end <= duration:
            raise ValueError("Word boundaries must be ordered and inside audio")
        previous = end
    return words


def _word_region(words, plan):
    kind = plan.get("corruption")
    if kind == "inserted_pause":
        index = plan.get("at_word_index")
        if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index < len(words):
            raise ValueError("Pause must be placed at an internal word boundary")
        return words[index]["start_seconds"], None
    start = plan.get("start_word_index")
    end = plan.get("end_word_index")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in (start, end)):
        raise ValueError("Corruption region needs integer word indexes")
    if not 0 <= start < end <= len(words):
        raise ValueError("Corruption region must cover complete words")
    return words[start]["start_seconds"], words[end - 1]["end_seconds"]


def _transform(samples, sample_rate, words, plan):
    kind = plan.get("corruption")
    if kind == "clean":
        if "severity" in plan:
            raise ValueError("Clean examples cannot have severity")
        return samples.copy(), [], None
    if kind == "control_global_gain":
        output, control = global_gain_control(samples, sample_rate, plan.get("variant"))
        return output, [], control
    severity = plan.get("severity")
    start, end = _word_region(words, plan)
    if kind == "quiet":
        method = plan.get("method", "hard_attenuation")
        if method == "hard_attenuation":
            output, label = quiet_region(samples, sample_rate, start, end, severity)
            label["parameters"]["method"] = method
        elif method == "cosine_envelope":
            output, label = smooth_quiet_region(samples, sample_rate, start, end, severity)
        else:
            raise ValueError("Unknown quiet method")
    elif kind == "rushed":
        output, label = rush_region(samples, sample_rate, start, end, severity)
    elif kind == "inserted_pause":
        output, label = insert_pause(samples, sample_rate, start, severity)
    else:
        raise ValueError("Unknown corruption")
    label["word_region"] = {key: plan[key] for key in
                            ("start_word_index", "end_word_index", "at_word_index") if key in plan}
    return output, [label], None


def _pcm_bytes(samples):
    clipped = np.clip(samples, -1.0, 1.0)
    return np.round(clipped * 32767).astype("<i2").tobytes()


def _write_wav(path, samples, sample_rate):
    pcm = _pcm_bytes(samples)
    with wave.open(str(path), "wb") as target:
        target.setnchannels(1)
        target.setsampwidth(2)
        target.setframerate(sample_rate)
        target.writeframes(pcm)
    return pcm


def build_dataset(output_dir, sources, plans):
    """Build audio plus separate detector and evaluation JSONL manifests."""
    root = Path(output_dir)
    if root.exists() and any(root.iterdir()):
        raise ValueError("Output directory must be absent or empty")
    if not sources or not plans:
        raise ValueError("Require sources and derivative plans")
    source_map = {}
    for source in sources:
        metadata = validate_source(source.get("metadata", {}))
        recording_id = metadata["recording_id"]
        if recording_id in source_map:
            raise ValueError("Duplicate recording_id")
        source_map[recording_id] = source

    partitions = {}
    for plan in plans:
        recording_id = plan.get("recording_id")
        partition = plan.get("partition")
        if recording_id not in source_map or partition not in ALLOWED_PARTITIONS:
            raise ValueError("Plan has unknown source or partition")
        existing = partitions.setdefault(recording_id, partition)
        if existing != partition:
            raise ValueError("All derivatives of one recording must share a partition")

    def method_signature(plan):
        defaults = {"quiet": "hard_attenuation", "rushed": "linear_resampling_pitch_shifting_baseline",
                    "inserted_pause": "silence_insertion"}
        return plan.get("corruption"), plan.get("method", defaults.get(plan.get("corruption"), "default"))

    held_out_methods = set()
    for plan in plans:
        if plan.get("holdout_method") is True:
            if plan["partition"] != "held_out":
                raise ValueError("A held-out corruption method may appear only in held_out")
            held_out_methods.add(method_signature(plan))
        elif plan.get("holdout_method") not in (None, False):
            raise ValueError("holdout_method must be boolean")
    for plan in plans:
        if plan["partition"] != "held_out" and method_signature(plan) in held_out_methods:
            raise ValueError("Held-out corruption method leaked into another partition")

    seen_by_partition = {}
    for recording_id, partition in partitions.items():
        metadata = validate_source(source_map[recording_id]["metadata"])
        bucket = seen_by_partition.setdefault(partition, {"speaker_id": set(), "text_id": set(),
                                                           "recording_id": set()})
        for field in bucket:
            bucket[field].add(metadata[field])
    partition_names = sorted(seen_by_partition)
    for left_index, left in enumerate(partition_names):
        for right in partition_names[left_index + 1:]:
            for field in ("speaker_id", "text_id", "recording_id"):
                if seen_by_partition[left][field] & seen_by_partition[right][field]:
                    raise ValueError(f"Partition leakage: {field}")

    # Validate and render every derivative before creating any output files.
    prepared = []
    provenance_records = {}
    detector_records, truth_records = [], []
    used_ids = set()
    for plan in plans:
        source = source_map[plan["recording_id"]]
        metadata = validate_source(source["metadata"])
        samples = load_audio(source["audio_path"])
        duration = len(samples) / 16000
        transcript = normalize_transcript(source["transcript"])
        words = _validate_words(source["words"], transcript, duration)
        output, labels, control = _transform(samples, 16000, words, plan)
        pcm = _pcm_bytes(output)
        source_hash = hashlib.sha256(Path(source["audio_path"]).read_bytes()).hexdigest()
        provenance_records[metadata["recording_id"]] = {
            "metadata": metadata, "source_file_sha256": source_hash,
            "transcript": transcript, "alignment_words": words,
            "alignment_claim": "supplied_word_spans_not_independently_validated_by_builder"}
        identity = {"format": FORMAT_VERSION, "source_sha256": source_hash,
                    "transcript": transcript, "alignment_words": words,
                    "recording_id": metadata["recording_id"], "partition": plan["partition"],
                    "plan": {key: plan[key] for key in sorted(plan) if key != "recording_id"},
                    "output_pcm_sha256": hashlib.sha256(pcm).hexdigest()}
        derivative_id = hashlib.sha256(_canonical(identity).encode()).hexdigest()
        if derivative_id in used_ids:
            raise ValueError("Duplicate derivative plan")
        used_ids.add(derivative_id)
        relative_audio = f"audio/{derivative_id}.wav"
        prepared.append((relative_audio, output, pcm))
        detector_records.append({"derivative_id": derivative_id, "audio_path": relative_audio,
                                 "partition": plan["partition"], "transcript": transcript,
                                 "duration_seconds": len(output) / 16000})
        truth_records.append({"derivative_id": derivative_id, "recording_id": metadata["recording_id"],
                              "speaker_id": metadata["speaker_id"], "text_id": metadata["text_id"],
                              "corruption": plan["corruption"], "labels": labels,
                              "control": control, "expected_flaw": bool(labels),
                              "provenance": "evaluation_only_never_detector_input"})

    audio_dir = root / "audio"
    audio_dir.mkdir(parents=True)
    for relative_audio, output, pcm in prepared:
        if _write_wav(root / relative_audio, output, 16000) != pcm:
            raise AssertionError("WAV serialization mismatch")
    (root / "source_provenance.json").write_text(_canonical(provenance_records) + "\n")
    detector_records.sort(key=lambda item: item["derivative_id"])
    truth_records.sort(key=lambda item: item["derivative_id"])
    (root / "detector_manifest.jsonl").write_text("".join(_canonical(item) + "\n" for item in detector_records))
    (root / "evaluation_truth.jsonl").write_text("".join(_canonical(item) + "\n" for item in truth_records))
    build = {"format": FORMAT_VERSION, "entries": len(detector_records),
             "source_provenance_sha256": hashlib.sha256((root / "source_provenance.json").read_bytes()).hexdigest(),
             "detector_manifest_sha256": hashlib.sha256((root / "detector_manifest.jsonl").read_bytes()).hexdigest(),
             "evaluation_truth_sha256": hashlib.sha256((root / "evaluation_truth.jsonl").read_bytes()).hexdigest()}
    (root / "build.json").write_text(json.dumps(build, indent=2, sort_keys=True) + "\n")
    return build
