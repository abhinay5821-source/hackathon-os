"""Explicitly synthetic fixtures for the ClearRoute feasibility tests."""

from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path

SIZE = (160, 240)
ROUTE = (70, 35, 170, 125)


def reference() -> np.ndarray:
    image = np.full((*SIZE, 3), 170, np.uint8)
    cv2.rectangle(image, (70, 35), (170, 125), (190, 190, 190), -1)
    cv2.line(image, (70, 35), (70, 125), (240, 240, 240), 2)
    cv2.line(image, (170, 35), (170, 125), (240, 240, 240), 2)
    return image


def scenario(name: str, count: int = 30) -> list[np.ndarray]:
    known = {"clear", "persistent_box", "transient_passage", "intermittent_obstruction", "outside_route", "poor_light", "gradual_dimming", "global_occlusion", "camera_shift", "slow_camera_drift", "shadow"}
    if name not in known:
        raise ValueError(f"Unknown synthetic scenario: {name}")
    base = reference()
    frames: list[np.ndarray] = []
    for index in range(count):
        frame = base.copy()
        if name == "persistent_box":
            cv2.rectangle(frame, (100, 65), (140, 110), (25, 80, 180), -1)
        elif name == "transient_passage" and 8 <= index < 15:
            x = 75 + (index - 8) * 12
            cv2.rectangle(frame, (x, 55), (x + 20, 115), (35, 35, 35), -1)
        elif name == "intermittent_obstruction" and index % 8 < 5:
            cv2.rectangle(frame, (100, 65), (140, 110), (25, 80, 180), -1)
        elif name == "outside_route":
            cv2.rectangle(frame, (10, 60), (50, 115), (25, 80, 180), -1)
        elif name == "poor_light":
            frame = np.full_like(frame, 25)
        elif name == "gradual_dimming":
            frame = cv2.convertScaleAbs(frame, alpha=max(0.35, 1.0 - index * 0.025), beta=0)
        elif name == "global_occlusion":
            frame[:, :180] = 20
        elif name == "camera_shift":
            matrix = np.float32([[1, 0, 12], [0, 1, 0]])
            frame = cv2.warpAffine(frame, matrix, (frame.shape[1], frame.shape[0]), borderValue=(0, 0, 0))
        elif name == "slow_camera_drift":
            shift = index // 3
            matrix = np.float32([[1, 0, shift], [0, 1, 0]])
            frame = cv2.warpAffine(frame, matrix, (frame.shape[1], frame.shape[0]), borderValue=(0, 0, 0))
        elif name == "shadow":
            overlay = frame.copy()
            cv2.rectangle(overlay, (75, 40), (165, 120), (115, 115, 115), -1)
            frame = cv2.addWeighted(overlay, 0.35, frame, 0.65, 0)
        frames.append(frame)
    return frames


def write_fixture_set(directory: Path, fps: float = 10.0) -> None:
    """Write synthetic AVI clips and their clear reference image."""
    directory.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(directory / "reference.png"), reference())
    for name in ("clear", "persistent_box", "transient_passage", "intermittent_obstruction", "outside_route", "poor_light", "gradual_dimming", "global_occlusion", "camera_shift", "slow_camera_drift", "shadow"):
        writer = cv2.VideoWriter(
            str(directory / f"{name}.avi"),
            cv2.VideoWriter_fourcc(*"MJPG"),
            fps,
            (SIZE[1], SIZE[0]),
        )
        if not writer.isOpened():
            raise RuntimeError("Synthetic video writer could not open MJPG codec")
        for frame in scenario(name):
            writer.write(frame)
        writer.release()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate clearly labeled synthetic ClearRoute clips")
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    write_fixture_set(args.directory)
