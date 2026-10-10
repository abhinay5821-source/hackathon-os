"""Fail closed unless a RepairLab Track C submission evidence bundle is complete."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse

from repairlab.freeze_rubric import verify_rubric_config


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _public_https(value, name):
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a public HTTPS URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.hostname in {"localhost", "127.0.0.1"}:
        raise ValueError(f"{name} must be a public HTTPS URL")


def _artifact(root, record, name):
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise ValueError(f"{name} artifact is required")
    path = (root / record["path"]).resolve()
    if root.resolve() not in path.parents or not path.is_file():
        raise ValueError(f"{name} artifact path is missing or escapes the bundle")
    digest = record.get("sha256")
    if not isinstance(digest, str) or digest != _sha(path):
        raise ValueError(f"{name} artifact SHA-256 mismatch")
    return path


def _finite_number(value, name, minimum=0.0, maximum=None):
    if (isinstance(value, bool) or not isinstance(value, (int, float)) or
            not math.isfinite(value) or value < minimum or
            (maximum is not None and value > maximum)):
        raise ValueError(f"{name} must be a finite number in the required range")


def _validate_alignment(report):
    if report.get("schema") != "repairlab-human-alignment-score-v1":
        raise ValueError("alignment_report lacks human alignment score schema")
    labelled = report.get("labelled_words")
    if isinstance(labelled, bool) or not isinstance(labelled, int) or labelled <= 0:
        raise ValueError("alignment_report requires labelled_words > 0")
    _finite_number(report.get("labelled_fraction"), "labelled_fraction", 0.0, 1.0)
    if report["labelled_fraction"] <= 0:
        raise ValueError("labelled_fraction must be positive")
    for name in ("start_mae_seconds", "end_mae_seconds",
                 "boundary_median_absolute_error_seconds",
                 "boundary_p95_absolute_error_seconds",
                 "boundary_max_absolute_error_seconds"):
        _finite_number(report.get(name), name)
    _finite_number(report.get("boundaries_within_100ms_fraction"),
                   "boundaries_within_100ms_fraction", 0.0, 1.0)
    if not (report["boundary_median_absolute_error_seconds"] <=
            report["boundary_p95_absolute_error_seconds"] <=
            report["boundary_max_absolute_error_seconds"]):
        raise ValueError("alignment_report boundary error quantiles are inconsistent")


def _validate_held(report, rubric):
    if report.get("schema") != "repairlab-frozen-held-out-score-v1" or report.get("partition") != "held_out":
        raise ValueError("held_out_report is not a frozen held-out score")
    identifiers = report.get("derivative_ids")
    if (not isinstance(identifiers, list) or not identifiers or
            any(not isinstance(value, str) or not value for value in identifiers)):
        raise ValueError("held_out_report requires nonempty derivative_ids")
    if report.get("rubric_config_sha256") != rubric["config_sha256"] or report.get("calibration_sha256") != rubric["calibration_sha256"]:
        raise ValueError("held_out_report fingerprint does not match frozen rubric")
    evaluation = report.get("report")
    if (not isinstance(evaluation, dict) or
            evaluation.get("schema") != "repairlab-detector-evaluation-v1" or
            not isinstance(evaluation.get("system"), dict) or
            not isinstance(evaluation.get("baselines"), dict) or
            not evaluation["baselines"]):
        raise ValueError("held_out_report requires nonempty detector and baseline measurements")


def validate_submission(root, manifest):
    """Validate artifact presence, hashes, formats, and Track C packaging limits."""
    root = Path(root)
    if manifest.get("schema") != "repairlab-track-c-submission-v1":
        raise ValueError("Unsupported submission manifest schema")
    _public_https(manifest.get("public_dataset_url"), "public_dataset_url")
    _public_https(manifest.get("video_url"), "video_url")
    pages = manifest.get("technical_document_pages")
    if isinstance(pages, bool) or not isinstance(pages, int) or not 1 <= pages <= 6:
        raise ValueError("technical_document_pages must be between 1 and 6")
    duration = manifest.get("video_duration_seconds")
    if (isinstance(duration, bool) or not isinstance(duration, (int, float)) or
            not math.isfinite(duration) or not 180 <= duration <= 600):
        raise ValueError("video_duration_seconds must be between 180 and 600")
    if manifest.get("video_english_or_subtitled") is not True:
        raise ValueError("Video must be English or subtitled")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("artifacts object is required")
    document = _artifact(root, artifacts.get("technical_document"), "technical_document")
    alignment_path = _artifact(root, artifacts.get("alignment_report"), "alignment_report")
    held_path = _artifact(root, artifacts.get("held_out_report"), "held_out_report")
    dataset_path = _artifact(root, artifacts.get("dataset_verification"), "dataset_verification")
    rubric_path = _artifact(root, artifacts.get("rubric_config"), "rubric_config")
    if document.suffix.lower() != ".pdf":
        raise ValueError("technical_document must be a PDF")
    alignment = json.loads(alignment_path.read_text())
    held = json.loads(held_path.read_text())
    dataset = json.loads(dataset_path.read_text())
    rubric = json.loads(rubric_path.read_text())
    verify_rubric_config(rubric)
    _validate_alignment(alignment)
    _validate_held(held, rubric)
    if dataset.get("verified") is not True or not isinstance(dataset.get("files"), dict) or not dataset["files"]:
        raise ValueError("dataset_verification is not a successful verification report")
    return {"evidence_bundle_valid": True, "schema": manifest["schema"], "checked_artifacts": 5,
            "limitations": ["PDF page count and video duration remain manifest declarations and must be checked against rendered media.",
                            "This gate does not prove listener benefit, URL reachability, eligibility, or submission acceptance."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    print(json.dumps(validate_submission(args.manifest.parent, manifest), sort_keys=True))


if __name__ == "__main__":
    main()
