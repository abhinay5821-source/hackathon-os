"""Fetch a small, reproducible VCTK subset without downloading the 11-GB ZIP."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


ARCHIVE_URL = "https://datashare.ed.ac.uk/server/api/core/bitstreams/535f4286-e54c-4038-838c-a02285e32cb2/content"
SOURCE_URL = "https://doi.org/10.7488/ds/2645"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


def member_names(speakers, text_id):
    speakers = list(speakers)
    if not 1 <= len(speakers) <= 10 or len(set(speakers)) != len(speakers):
        raise ValueError("Choose 1-10 unique speakers")
    if not re.fullmatch(r"\d{3}", text_id):
        raise ValueError("text_id must contain exactly three digits")
    for speaker in speakers:
        if not re.fullmatch(r"p\d{3}", speaker):
            raise ValueError(f"Invalid speaker ID: {speaker}")
    return [
        name
        for speaker in speakers
        for name in (
            f"txt/{speaker}/{speaker}_{text_id}.txt",
            f"wav48_silence_trimmed/{speaker}/{speaker}_{text_id}_mic1.flac",
        )
    ]


def fetch_subset(output, speakers, text_id):
    from remotezip import RemoteZip

    output = Path(output)
    requested = member_names(speakers, text_id)
    records = []
    with RemoteZip(ARCHIVE_URL) as archive:
        available = set(archive.namelist())
        missing = sorted(set(requested) - available)
        if missing:
            raise ValueError(f"Requested VCTK members are absent: {missing}")
        for member in requested:
            data = archive.read(member)
            target = output / member
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            records.append({"member": member, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    manifest = {
        "source": SOURCE_URL,
        "archive_url": ARCHIVE_URL,
        "license": "CC-BY-4.0",
        "license_url": LICENSE_URL,
        "attribution": "CSTR VCTK Corpus 0.92, Yamagishi, Veaux and MacDonald, University of Edinburgh, DOI 10.7488/ds/2645",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "text_id": text_id,
        "speakers": list(speakers),
        "files": records,
        "claim_limit": "Clean read speech for alignment/acoustic validation; not an expert-delivery score or clinical reference.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--speakers", nargs="+", required=True)
    parser.add_argument("--text-id", default="001")
    args = parser.parse_args()
    result = fetch_subset(args.output, args.speakers, args.text_id)
    print(json.dumps({"files": len(result["files"]), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
