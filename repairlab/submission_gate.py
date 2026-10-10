"""Fail closed unless a RepairLab Track C submission evidence bundle is complete."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlparse


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
    if document.suffix.lower() != ".pdf":
        raise ValueError("technical_document must be a PDF")
    alignment = json.loads(alignment_path.read_text())
    held = json.loads(held_path.read_text())
    dataset = json.loads(dataset_path.read_text())
    if alignment.get("schema") != "repairlab-human-alignment-score-v1":
        raise ValueError("alignment_report lacks human alignment score schema")
    if held.get("schema") != "repairlab-frozen-held-out-score-v1" or held.get("partition") != "held_out":
        raise ValueError("held_out_report is not a frozen held-out score")
    if dataset.get("verified") is not True or not isinstance(dataset.get("files"), dict) or not dataset["files"]:
        raise ValueError("dataset_verification is not a successful verification report")
    return {"ready": True, "schema": manifest["schema"], "checked_artifacts": 4,
            "limitations": ["This gate verifies declared files and packaging constraints; it does not prove listener benefit or submission acceptance."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    print(json.dumps(validate_submission(args.manifest.parent, manifest), sort_keys=True))


if __name__ == "__main__":
    main()
