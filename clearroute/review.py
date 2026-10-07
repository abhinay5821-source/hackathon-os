"""Generate a self-contained, offline human-review page from an analysis result."""

from __future__ import annotations

import argparse
import base64
import html
import json
from pathlib import Path


def render_review(result: dict, result_directory: Path) -> str:
    status = html.escape(str(result.get("status", "unknown")))
    reason = html.escape(str(result.get("reason", "unknown")))
    warning = html.escape(str(result.get("warning", "Prototype output.")))
    image_markup = "<p>No evidence image was produced for this outcome.</p>"
    image_name = result.get("evidence_image")
    if image_name:
        image_path = Path(image_name)
        if not image_path.is_absolute():
            image_path = result_directory / image_path
        if image_path.exists():
            encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
            image_markup = f'<img src="data:image/png;base64,{encoded}" alt="Marked evidence frame">'

    timestamp = result.get("evidence_timestamp_seconds")
    timestamp_text = "—" if timestamp is None else f"{float(timestamp):.3f} s"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>ClearRoute review</title><style>
body{{font-family:system-ui,sans-serif;max-width:860px;margin:40px auto;padding:0 20px;background:#111;color:#eee}}
.card{{background:#1b1b1b;border:1px solid #444;border-radius:12px;padding:20px;margin:16px 0}}
.status{{font-size:1.5rem;font-weight:700}} img{{max-width:100%;border:2px solid #d44}}
dt{{color:#aaa}} dd{{margin:0 0 12px}} .warning{{color:#ffd479}}
</style></head><body><h1>ClearRoute human review</h1>
<div class="card"><div class="status">{status}</div><p>{reason}</p>
<dl><dt>Evidence frame</dt><dd>{html.escape(str(result.get("evidence_frame", "—")))}</dd>
<dt>Timestamp</dt><dd>{timestamp_text}</dd>
<dt>Longest observed run</dt><dd>{html.escape(str(result.get("longest_obstruction_frames", "—")))} frames</dd></dl></div>
<div class="card"><h2>Evidence</h2>{image_markup}</div>
<div class="card warning"><strong>Limit:</strong> {warning} A person must inspect the source video and physical route.</div>
</body></html>"""


def write_review(result_path: Path, output_path: Path) -> Path:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_review(result, result_path.parent), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an offline ClearRoute review page")
    parser.add_argument("result", type=Path)
    parser.add_argument("--output", type=Path, default=Path("clearroute-review.html"))
    args = parser.parse_args()
    print(write_review(args.result, args.output))


if __name__ == "__main__":
    main()
