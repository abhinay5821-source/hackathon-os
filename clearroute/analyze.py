"""Deterministic OpenCV baseline for a configured route polygon.

This module produces review evidence, not a safety decision. It intentionally
does not identify or track people.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np


@dataclass(frozen=True)
class AnalysisConfig:
    route: tuple[int, int, int, int] = (70, 35, 170, 125)
    difference_threshold: int = 28
    occupied_fraction: float = 0.08
    persistence_frames: int = 12
    minimum_brightness: float = 45.0
    maximum_global_change: float = 0.55
    maximum_registration_shift: float = 5.0
    reflection_value_threshold: float = 245.0
    reflection_saturation_threshold: float = 20.0
    fps: float = 10.0


def _mask(shape: tuple[int, ...], route: tuple[int, int, int, int]) -> np.ndarray:
    x1, y1, x2, y2 = route
    result = np.zeros(shape[:2], dtype=np.uint8)
    result[y1:y2, x1:x2] = 255
    return result


def _shift(reference_gray: np.ndarray, frame_gray: np.ndarray) -> float:
    window = cv2.createHanningWindow(
        (reference_gray.shape[1], reference_gray.shape[0]), cv2.CV_32F
    )
    (dx, dy), _ = cv2.phaseCorrelate(
        reference_gray.astype(np.float32), frame_gray.astype(np.float32), window
    )
    return float((dx * dx + dy * dy) ** 0.5)


def analyze_frames(
    reference: np.ndarray,
    frames: Iterable[np.ndarray],
    config: AnalysisConfig = AnalysisConfig(),
) -> dict:
    """Classify a stream and return JSON-safe evidence metadata."""
    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    route_mask = _mask(reference.shape, config.route)
    kernel = np.ones((5, 5), np.uint8)
    run = longest_run = reflection_run = 0
    evidence_index: int | None = None
    occupancies: list[float] = []

    for index, frame in enumerate(frames):
        if frame.shape != reference.shape:
            return _result("uncertain", "frame_size_changed", index, None, occupancies, config)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if float(gray.mean()) < config.minimum_brightness:
            return _result("uncertain", "poor_light", index, None, occupancies, config)
        if _shift(reference_gray, gray) > config.maximum_registration_shift:
            return _result("uncertain", "camera_shift", index, None, occupancies, config)

        diff = cv2.absdiff(reference_gray, gray)
        changed = cv2.threshold(diff, config.difference_threshold, 255, cv2.THRESH_BINARY)[1]
        global_fraction = float(np.count_nonzero(changed)) / changed.size
        if global_fraction > config.maximum_global_change:
            return _result("uncertain", "global_illumination_or_occlusion", index, None, occupancies, config)
        changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, kernel)
        route_pixels = cv2.bitwise_and(changed, route_mask)
        fraction = float(np.count_nonzero(route_pixels)) / float(np.count_nonzero(route_mask))
        occupancies.append(round(fraction, 5))
        if fraction >= config.occupied_fraction:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            changed_inside = route_pixels > 0
            mean_saturation = float(hsv[:, :, 1][changed_inside].mean())
            mean_value = float(hsv[:, :, 2][changed_inside].mean())
            reflection_like = (
                mean_value >= config.reflection_value_threshold
                and mean_saturation <= config.reflection_saturation_threshold
            )
            reflection_run = reflection_run + 1 if reflection_like else 0
            if reflection_run >= config.persistence_frames:
                return _result("uncertain", "possible_reflection", index + 1, None, occupancies, config)
            run += 1
            if run >= config.persistence_frames and evidence_index is None:
                evidence_index = index
            longest_run = max(longest_run, run)
        else:
            run = 0
            reflection_run = 0

    if not occupancies:
        return _result("uncertain", "no_frames", 0, None, occupancies, config)
    if longest_run >= config.persistence_frames:
        return _result("review_required", "persistent_route_obstruction", len(occupancies), evidence_index, occupancies, config)
    return _result("clear", "no_persistent_obstruction", len(occupancies), None, occupancies, config)


def _result(status, reason, frame_count, evidence_index, occupancies, config):
    return {
        "status": status,
        "reason": reason,
        "frame_count": frame_count,
        "evidence_frame": evidence_index,
        "evidence_timestamp_seconds": (
            round(evidence_index / config.fps, 3) if evidence_index is not None else None
        ),
        "longest_obstruction_frames": _longest_run(occupancies, config.occupied_fraction),
        "occupancy_by_frame": occupancies,
        "config": asdict(config),
        "warning": "Synthetic prototype; human review required; not a safety control.",
    }


def _longest_run(values: list[float], threshold: float) -> int:
    longest = current = 0
    for value in values:
        current = current + 1 if value >= threshold else 0
        longest = max(longest, current)
    return longest


def analyze_video(reference_path: Path, video_path: Path, output_path: Path, config=AnalysisConfig()) -> dict:
    reference = cv2.imread(str(reference_path))
    if reference is None:
        raise ValueError(f"Cannot read reference image: {reference_path}")
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Cannot read video: {video_path}")

    def stream():
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame

    try:
        result = analyze_frames(reference, stream(), config)
    finally:
        capture.release()
    evidence_index = result["evidence_frame"]
    if evidence_index is not None:
        capture = cv2.VideoCapture(str(video_path))
        capture.set(cv2.CAP_PROP_POS_FRAMES, evidence_index)
        ok, evidence = capture.read()
        capture.release()
        if ok:
            x1, y1, x2, y2 = config.route
            cv2.rectangle(evidence, (x1, y1), (x2, y2), (0, 0, 255), 2)
            evidence_path = output_path.with_suffix(".evidence.png")
            cv2.imwrite(str(evidence_path), evidence)
            result["evidence_image"] = str(evidence_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="ClearRoute local review prototype")
    parser.add_argument("reference", type=Path)
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, default=Path("clearroute-result.json"))
    args = parser.parse_args()
    print(json.dumps(analyze_video(args.reference, args.video, args.output), indent=2))


if __name__ == "__main__":
    main()
