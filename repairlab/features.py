"""Deterministic acoustic features and speaker-normalized word comparisons.

This is a transparent mathematical baseline. Its thresholds require held-out
calibration before any delivery-quality claim.
"""
import math

import numpy as np


FEATURES = ("energy_db", "f0_hz", "spectral_centroid_hz", "zero_crossing_rate",
            "duration_seconds", "preceding_pause_seconds")
MIN_SCALES = {"energy_db": 1.0, "f0_hz": 5.0, "spectral_centroid_hz": 50.0,
              "zero_crossing_rate": 0.01, "duration_seconds": 0.02,
              "preceding_pause_seconds": 0.02}
FEATURE_UNITS = {"energy_db": "dB", "f0_hz": "Hz", "spectral_centroid_hz": "Hz",
                 "zero_crossing_rate": "ratio", "duration_seconds": "seconds",
                 "preceding_pause_seconds": "seconds"}


def _feedback(candidate_type, row, baseline_row, flagged):
    """Separate measurement from conservative interpretation and rehearsal action."""
    if candidate_type == "inserted_pause":
        gap = row["preceding_pause_seconds"] - baseline_row["preceding_pause_seconds"]
        return ("The pause before this word is longer than the transcript-matched reference.",
                f"Replay {row['start_seconds']:.2f}–{row['end_seconds']:.2f}s and rehearse the "
                f"transition with about {abs(gap):.2f}s less pause, then re-record and compare.",
                "Measured participant-minus-reference pause difference; reference evidence, not a universal optimum.")
    if candidate_type == "rushed":
        gap = row["duration_seconds"] - baseline_row["duration_seconds"]
        return ("This word is shorter than the transcript-matched reference.",
                f"Replay {row['start_seconds']:.2f}–{row['end_seconds']:.2f}s and rehearse the word "
                f"about {abs(gap):.2f}s longer, then re-record and compare.",
                "Measured participant-minus-reference duration difference; reference evidence, not a universal optimum.")
    if candidate_type == "quiet":
        gap = row["energy_db"] - baseline_row["energy_db"]
        return ("Local energy is lower than the transcript-matched reference after within-recording normalization.",
                f"Replay {row['start_seconds']:.2f}–{row['end_seconds']:.2f}s and test a more projected "
                f"delivery; the raw local energy difference is {gap:+.2f} dB.",
                "Measured energy difference. Microphone distance and room acoustics can also cause it.")
    features = ", ".join(sorted(flagged))
    return (f"Acoustic deviation detected in {features}, but this baseline cannot justify a delivery flaw label.",
            "Review the marked audio in context; no automatic correction is recommended.",
            "Abstention: acoustic difference alone is not evidence of poor delivery.")


def _waveform(samples, sample_rate):
    values = np.asarray(samples)
    if values.ndim != 1 or values.size == 0 or not np.issubdtype(values.dtype, np.floating):
        raise ValueError("Require a nonempty one-dimensional floating-point waveform")
    if not np.isfinite(values).all() or np.max(np.abs(values)) > 1.0:
        raise ValueError("Waveform must contain finite normalized samples in [-1, 1]")
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, (int, np.integer)) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")
    return values.astype(np.float64, copy=False), int(sample_rate)


def _pitch(frame, sample_rate, energy_db):
    if energy_db < -55.0:
        return math.nan
    centered = frame - np.mean(frame)
    denominator = float(np.dot(centered, centered))
    if denominator <= 1e-12:
        return math.nan
    correlation = np.correlate(centered, centered, mode="full")[len(centered) - 1:]
    minimum_lag = max(1, math.floor(sample_rate / 400.0))
    maximum_lag = min(len(frame) - 1, math.ceil(sample_rate / 70.0))
    if minimum_lag >= maximum_lag:
        return math.nan
    candidates = correlation[minimum_lag:maximum_lag + 1]
    lag = minimum_lag + int(np.argmax(candidates))
    confidence = correlation[lag] / denominator
    return sample_rate / lag if confidence >= 0.30 else math.nan


def extract_frame_features(samples, sample_rate=16000, frame_seconds=0.025, hop_seconds=0.010):
    """Extract energy, pitch, spectral centroid and zero-crossing rate."""
    values, rate = _waveform(samples, sample_rate)
    frame_length = round(frame_seconds * rate)
    hop_length = round(hop_seconds * rate)
    if frame_length < 2 or hop_length < 1:
        raise ValueError("Frame and hop durations are too short")
    if len(values) < frame_length:
        values = np.pad(values, (0, frame_length - len(values)))
    starts = np.arange(0, len(values) - frame_length + 1, hop_length, dtype=int)
    window = np.hanning(frame_length)
    frequencies = np.fft.rfftfreq(frame_length, 1.0 / rate)
    output = {name: [] for name in FEATURES[:4]}
    for start in starts:
        frame = values[start:start + frame_length]
        energy_db = 10.0 * math.log10(float(np.mean(frame * frame)) + 1e-12)
        spectrum = np.abs(np.fft.rfft(frame * window))
        magnitude = float(np.sum(spectrum))
        centroid = float(np.sum(frequencies * spectrum) / magnitude) if magnitude > 1e-12 else 0.0
        signs = np.signbit(frame)
        output["energy_db"].append(energy_db)
        output["f0_hz"].append(_pitch(frame, rate, energy_db))
        output["spectral_centroid_hz"].append(centroid)
        output["zero_crossing_rate"].append(float(np.mean(signs[1:] != signs[:-1])))
    result = {name: np.asarray(values_, dtype=float) for name, values_ in output.items()}
    result["frame_start_seconds"] = starts / rate
    result["frame_center_seconds"] = (starts + frame_length / 2.0) / rate
    result["frame_seconds"] = frame_length / rate
    result["hop_seconds"] = hop_length / rate
    return result


def summarize_words(frame_features, words):
    """Aggregate frame features inside aligned word intervals."""
    centers = np.asarray(frame_features.get("frame_center_seconds"))
    if centers.ndim != 1 or centers.size == 0:
        raise ValueError("Require nonempty frame features")
    summaries = []
    previous_end = 0.0
    for item in words:
        word, start, end = item.get("word"), item.get("start_seconds"), item.get("end_seconds")
        if not isinstance(word, str) or not word or not all(isinstance(v, (int, float)) for v in (start, end)):
            raise ValueError("Invalid aligned word")
        if not previous_end <= start < end:
            raise ValueError("Word intervals must be ordered and nonoverlapping")
        mask = (centers >= start) & (centers <= end)
        if not np.any(mask):
            raise ValueError("Word interval contains no feature frame centers")
        summary = {"word": word, "start_seconds": float(start), "end_seconds": float(end),
                   "duration_seconds": float(end - start),
                   "preceding_pause_seconds": float(start - previous_end)}
        for feature in FEATURES[:4]:
            selected = np.asarray(frame_features[feature])[mask]
            finite = selected[np.isfinite(selected)]
            summary[feature] = float(np.median(finite)) if finite.size else None
        summaries.append(summary)
        previous_end = end
    return summaries


def _normalization(rows, feature):
    values = np.asarray([math.nan if row[feature] is None else row[feature] for row in rows], dtype=float)
    finite = values[np.isfinite(values)]
    if not finite.size:
        return values, {"center": None, "scale": None, "method": "median/MAD"}
    center = float(np.median(finite))
    mad = float(np.median(np.abs(finite - center)))
    scale = max(1.4826 * mad, MIN_SCALES[feature])
    return (values - center) / scale, {"center": center, "scale": scale, "method": "median/MAD_floor"}


def compare_word_features(baseline, participant, threshold=2.5, active_features=None):
    """Return timestamped regions whose within-speaker feature deltas exceed a threshold."""
    if len(baseline) != len(participant) or len(baseline) < 3:
        raise ValueError("Require at least three transcript-matched words")
    if not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("threshold must be positive and finite")
    active = tuple(FEATURES if active_features is None else active_features)
    if not active or len(set(active)) != len(active) or any(item not in FEATURES for item in active):
        raise ValueError("active_features must be unique supported feature names")
    for expected, observed in zip(baseline, participant):
        if expected.get("word") != observed.get("word"):
            raise ValueError("Baseline and participant words must match")
    normalized = {}
    parameters = {}
    for feature in active:
        base_z, base_parameters = _normalization(baseline, feature)
        participant_z, participant_parameters = _normalization(participant, feature)
        normalized[feature] = participant_z - base_z
        parameters[feature] = {"baseline": base_parameters, "participant": participant_parameters}
    regions = []
    for index, row in enumerate(participant):
        deltas = {feature: float(normalized[feature][index]) for feature in active
                  if np.isfinite(normalized[feature][index])}
        flagged = {feature: delta for feature, delta in deltas.items() if abs(delta) >= threshold}
        if not flagged:
            continue
        explanations = [
            f"{feature}: participant normalized value minus baseline normalized value = {delta:+.2f}; "
            f"absolute delta >= {threshold:.2f}."
            for feature, delta in sorted(flagged.items())
        ]
        candidates = []
        if flagged.get("preceding_pause_seconds", 0.0) > 0:
            candidates.append((abs(flagged["preceding_pause_seconds"]), "inserted_pause"))
        if flagged.get("duration_seconds", 0.0) < 0:
            candidates.append((abs(flagged["duration_seconds"]), "rushed"))
        if flagged.get("energy_db", 0.0) < 0:
            candidates.append((abs(flagged["energy_db"]), "quiet"))
        candidate_type = max(candidates)[1] if candidates else "unclassified_acoustic_deviation"
        evidence = [{"feature": feature, "unit": FEATURE_UNITS[feature],
                     "baseline_value": baseline[index].get(feature),
                     "participant_value": row.get(feature),
                     "normalized_delta": delta, "threshold": float(threshold)}
                    for feature, delta in sorted(flagged.items())]
        interpretation, action, action_basis = _feedback(
            candidate_type, row, baseline[index], flagged)
        regions.append({"word_index": index, "word": row["word"],
                        "start_seconds": row["start_seconds"], "end_seconds": row["end_seconds"],
                        "max_absolute_delta": max(abs(value) for value in flagged.values()),
                        "feature_deltas": flagged, "candidate_flaw_type": candidate_type,
                        "explanations": explanations, "evidence": evidence,
                        "interpretation": interpretation, "suggested_action": action,
                        "action_basis": action_basis})
    return {"threshold": float(threshold), "active_features": list(active),
            "normalization": parameters, "regions": regions,
            "claim": "Transparent baseline; thresholds and delivery meaning require held-out calibration."}
