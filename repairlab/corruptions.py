"""Deterministic synthetic speech corruptions with exact output-time labels.

Labels returned here are generator truth and must never be passed to a detector.
They are evaluation metadata only.
"""
import math

import numpy as np


QUIET_DB = {"mild": 6.0, "medium": 12.0, "severe": 20.0}
PAUSE_SECONDS = {"mild": 0.20, "medium": 0.45, "severe": 0.80}
RUSH_FACTOR = {"mild": 1.15, "medium": 1.35, "severe": 1.65}
GLOBAL_GAIN_DB = {"lower": -3.0, "raise": 3.0}
VIBRATO = {"subtle": {"depth_cents": 20.0, "rate_hz": 4.5},
           "moderate": {"depth_cents": 35.0, "rate_hz": 5.5}}
FLAT_PITCH_STRENGTH = {"mild": 0.35, "medium": 0.65, "severe": 1.0}


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


def smooth_quiet_region(samples, sample_rate, start_seconds, end_seconds, severity):
    """Reduce amplitude with a cosine envelope as an alternate quiet method."""
    values, rate = _audio(samples, sample_rate)
    if severity not in QUIET_DB:
        raise ValueError("Unknown quiet severity")
    start, end = _region(start_seconds, end_seconds, rate, len(values))
    decibels = QUIET_DB[severity]
    minimum = 10 ** (-decibels / 20)
    phase = np.linspace(0.0, 2.0 * np.pi, end - start, endpoint=False)
    envelope = minimum + (1.0 - minimum) * (1.0 + np.cos(phase)) / 2.0
    values[start:end] *= envelope.astype(np.float32)
    return values, _label("quiet", severity, start, end, rate,
                          {"attenuation_db": decibels, "method": "cosine_envelope"})


def global_gain_control(samples, sample_rate, variant):
    """Apply a modest whole-clip gain change intended as a negative control."""
    values, rate = _audio(samples, sample_rate)
    if variant not in GLOBAL_GAIN_DB:
        raise ValueError("Unknown global-gain variant")
    decibels = GLOBAL_GAIN_DB[variant]
    output = values * (10 ** (decibels / 20))
    if np.max(np.abs(output)) > 1.0:
        raise ValueError("Global gain would clip; choose a lower-amplitude source")
    return output.astype(np.float32), {
        "control_type": "global_gain",
        "variant": variant,
        "parameters": {"gain_db": decibels},
        "expected_flaw": False,
        "provenance": "synthetic_negative_control_not_detector_input",
    }


def global_vibrato_control(samples, sample_rate, variant):
    """Apply a small deterministic whole-clip pitch modulation as a negative control.

    A monotonic time warp approximates vibrato while preserving sample count. It
    is not a studio-quality pitch shifter and must be reported as synthetic.
    """
    values, rate = _audio(samples, sample_rate)
    if variant not in VIBRATO:
        raise ValueError("Unknown vibrato variant")
    parameters = VIBRATO[variant]
    time = np.arange(len(values), dtype=np.float64) / rate
    ratio = 2.0 ** ((parameters["depth_cents"] *
                     np.sin(2.0 * np.pi * parameters["rate_hz"] * time)) / 1200.0)
    positions = np.cumsum(ratio)
    positions -= positions[0]
    if positions[-1] <= 0:
        raise ValueError("Vibrato warp is degenerate")
    positions *= (len(values) - 1) / positions[-1]
    output = np.interp(positions, np.arange(len(values)), values).astype(np.float32)
    return output, {
        "control_type": "global_pitch_vibrato",
        "variant": variant,
        "parameters": {**parameters, "method": "monotonic_time_warp"},
        "expected_flaw": False,
        "provenance": "synthetic_negative_control_not_detector_input",
    }


def flat_pitch_region(samples, sample_rate, start_seconds, end_seconds, severity):
    """Reduce estimated F0 movement with a deterministic local time warp.

    This is a CPU baseline, not a studio-quality pitch shifter. It uses only
    acoustic estimates from the selected region and returns exact generator
    labels; listener naturalness must be evaluated separately.
    """
    from repairlab.features import extract_frame_features

    values, rate = _audio(samples, sample_rate)
    if severity not in FLAT_PITCH_STRENGTH:
        raise ValueError("Unknown flat-pitch severity")
    start, end = _region(start_seconds, end_seconds, rate, len(values))
    source = values[start:end]
    features = extract_frame_features(source, rate, frame_seconds=0.04, hop_seconds=0.01)
    times = np.asarray(features["frame_center_seconds"], dtype=float) * rate
    pitches = np.asarray(features["f0_hz"], dtype=float)
    finite = np.isfinite(pitches)
    if np.count_nonzero(finite) < 3:
        raise ValueError("Flat-pitch region needs at least three voiced pitch frames")
    target = float(np.median(pitches[finite]))
    sample_positions = np.arange(len(source), dtype=float)
    track = np.interp(sample_positions, times[finite], pitches[finite],
                      left=pitches[finite][0], right=pitches[finite][-1])
    strength = FLAT_PITCH_STRENGTH[severity]
    ratio = np.power(target / np.maximum(track, 1e-6), strength)
    warped_positions = np.cumsum(ratio)
    warped_positions -= warped_positions[0]
    if warped_positions[-1] <= 0:
        raise ValueError("Flat-pitch warp is degenerate")
    warped_positions *= (len(source) - 1) / warped_positions[-1]
    transformed = np.interp(warped_positions, sample_positions, source).astype(np.float32)
    output = values.copy(); output[start:end] = transformed
    return output, _label("flat_pitch", severity, start, end, rate,
                          {"strength": strength, "target_f0_hz": target,
                           "method": "autocorrelation_guided_monotonic_time_warp",
                           "claim_limit": "synthetic CPU approximation; naturalness unvalidated"})


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
