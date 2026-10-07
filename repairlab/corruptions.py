"""Deterministic synthetic speech corruptions with exact output-time labels.

Labels returned here are generator truth and must never be passed to a detector.
They are evaluation metadata only.
"""
import math

import numpy as np


QUIET_DB = {"mild": 6.0, "medium": 12.0, "severe": 20.0}
PAUSE_SECONDS = {"mild": 0.20, "medium": 0.45, "severe": 0.80}
RUSH_FACTOR = {"mild": 1.15, "medium": 1.35, "severe": 1.65}


def _audio(samples, sample_rate):
    values = np.asarray(samples)
    if values.ndim != 1 or values.size == 0 or not np.issubdtype(values.dtype, np.floating):
        raise ValueError("Require a nonempty one-dimensional floating-point waveform")
    if not np.isfinite(values).all() or np.max(np.abs(values)) > 1.0:
        raise ValueError("Waveform must contain finite normalized samples in [-1, 1]")
    if isinstance(sample_rate, bool) or not isinstance(sample_rate, (int, np.integer)) or sample_rate <= 0:
        raise ValueError("sample_rate must be a positive integer")
    return values.astype(np.float32, copy=True), int(sample_rate)


def _region(start_seconds, end_seconds, sample_rate, length):
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in (start_seconds, end_seconds)):
        raise ValueError("Region boundaries must be finite numbers")
    start = round(start_seconds * sample_rate)
    end = round(end_seconds * sample_rate)
    if not 0 <= start < end <= length:
        raise ValueError("Region must be nonempty and inside the waveform")
    return start, end


def _label(kind, severity, start, end, sample_rate, parameters):
    return {
        "flaw_type": kind,
        "severity": severity,
        "start_sample": start,
        "end_sample": end,
        "start_seconds": start / sample_rate,
        "end_seconds": end / sample_rate,
        "parameters": parameters,
        "provenance": "synthetic_generator_truth_not_detector_input",
    }


def quiet_region(samples, sample_rate, start_seconds, end_seconds, severity):
    """Reduce amplitude inside one region without changing duration."""
    values, rate = _audio(samples, sample_rate)
    if severity not in QUIET_DB:
        raise ValueError("Unknown quiet severity")
    start, end = _region(start_seconds, end_seconds, rate, len(values))
    decibels = QUIET_DB[severity]
    values[start:end] *= 10 ** (-decibels / 20)
    return values, _label("quiet", severity, start, end, rate, {"attenuation_db": decibels})


def insert_pause(samples, sample_rate, at_seconds, severity):
    """Insert an exact-duration silent pause at a declared source position."""
    values, rate = _audio(samples, sample_rate)
    if severity not in PAUSE_SECONDS:
        raise ValueError("Unknown pause severity")
    if not isinstance(at_seconds, (int, float)) or not math.isfinite(at_seconds):
        raise ValueError("Pause position must be finite")
    at = round(at_seconds * rate)
    if not 0 <= at <= len(values):
        raise ValueError("Pause position must be inside the waveform")
    pause_samples = round(PAUSE_SECONDS[severity] * rate)
    output = np.concatenate((values[:at], np.zeros(pause_samples, dtype=np.float32), values[at:]))
    return output, _label("inserted_pause", severity, at, at + pause_samples, rate,
                          {"inserted_samples": pause_samples, "source_position_seconds": at / rate})


def rush_region(samples, sample_rate, start_seconds, end_seconds, severity):
    """Time-compress a region using deterministic linear resampling.

    This baseline changes pitch and must not be the only rush corruption used in
    held-out evaluation. A pitch-preserving alternative is a required follow-up.
    """
    values, rate = _audio(samples, sample_rate)
    if severity not in RUSH_FACTOR:
        raise ValueError("Unknown rush severity")
    start, end = _region(start_seconds, end_seconds, rate, len(values))
    factor = RUSH_FACTOR[severity]
    source = values[start:end]
    output_length = max(1, round(len(source) / factor))
    positions = np.linspace(0, len(source) - 1, output_length)
    compressed = np.interp(positions, np.arange(len(source)), source).astype(np.float32)
    output = np.concatenate((values[:start], compressed, values[end:]))
    return output, _label("rushed", severity, start, start + output_length, rate,
                          {"speed_factor": factor, "method": "linear_resampling_pitch_shifting_baseline",
                           "source_start_sample": start, "source_end_sample": end})
