"""Verify every frozen RepairLab dataset artifact against build.json."""
import argparse
import hashlib
import json
from pathlib import Path


FILES = {
    "source_provenance_sha256": "source_provenance.json",
    "detector_manifest_sha256": "detector_manifest.jsonl",
    "evaluation_truth_sha256": "evaluation_truth.jsonl",
}


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_dataset(root):
    root = Path(root)
    build_path = root / "build.json"
    if not build_path.is_file():
        raise ValueError("Dataset is missing build.json")
    try:
        build = json.loads(build_path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("build.json is not valid UTF-8 JSON") from exc

    checked = {}
    for key, name in FILES.items():
        path = root / name
        if not path.is_file() or not isinstance(build.get(key), str):
            raise ValueError(f"Dataset is missing a declared hash or file: {name}")
        actual = _sha256(path)
        if actual != build[key]:
            raise ValueError(f"Dataset hash mismatch: {name}")
        checked[name] = actual

    declared = build.get("audio_files_sha256")
    if not isinstance(declared, dict) or not declared or any(
            not isinstance(name, str) or not isinstance(digest, str)
            for name, digest in declared.items()):
        raise ValueError("build.json needs nonempty audio_files_sha256")
    audio_dir = root / "audio"
    actual_names = {path.name for path in audio_dir.glob("*.wav")} if audio_dir.is_dir() else set()
    if actual_names != set(declared):
        raise ValueError("Dataset audio file set does not match build.json")
    for name in sorted(declared):
        actual = _sha256(audio_dir / name)
        if actual != declared[name]:
            raise ValueError(f"Dataset hash mismatch: audio/{name}")
        checked[f"audio/{name}"] = actual
    return {"verified": True, "files": checked}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(verify_dataset(args.dataset), sort_keys=True))


if __name__ == "__main__":
    main()
