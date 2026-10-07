"""Generate one reproducible, explicitly synthetic ClearRoute judge demo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyze import AnalysisConfig, analyze_video
from .fixtures import ROUTE, write_fixture_set
from .review import write_review


def build_demo(output_directory: Path) -> dict:
    output_directory.mkdir(parents=True, exist_ok=True)
    fixtures = output_directory / "synthetic-fixtures"
    write_fixture_set(fixtures)
    result_path = output_directory / "clearroute-result.json"
    result = analyze_video(
        fixtures / "reference.png",
        fixtures / "persistent_box.avi",
        result_path,
        AnalysisConfig(route=ROUTE),
    )
    review_path = write_review(result_path, output_directory / "clearroute-review.html")
    return {
        "dataset_kind": "synthetic",
        "scenario": "persistent_box",
        "status": result["status"],
        "result": str(result_path),
        "evidence": result.get("evidence_image"),
        "review": str(review_path),
        "claim": "Reproducible synthetic demonstration only; not real-camera validation.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the synthetic ClearRoute demonstration bundle")
    parser.add_argument("--output", type=Path, default=Path("clearroute-demo"))
    args = parser.parse_args()
    print(json.dumps(build_demo(args.output), indent=2))


if __name__ == "__main__":
    main()
