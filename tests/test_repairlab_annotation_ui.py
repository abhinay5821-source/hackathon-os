import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from repairlab.annotation_ui import handler_for, load_package


def package(root):
    root.mkdir(); (root / "audio.wav").write_bytes(b"RIFF fake fixture")
    (root / "manifest.json").write_text(json.dumps({
        "format": "repairlab-blind-annotation-v1", "clip_id": "clip-a",
        "audio_sha256": "a" * 64, "prediction_included": False,
        "selected_words": [{"word_index": 0, "word": "WE"}, {"word_index": 2, "word": "MOON"}],
    }))


class AnnotationUiTests(unittest.TestCase):
    def test_page_contains_workflow_without_model_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            page, audio = load_package(root)
            for marker in (b"RepairLab blind annotation", b"Set start", b"Set end", b"prediction_hidden", b"Download completed JSON"):
                self.assertIn(marker, page)
            self.assertNotIn(b"start_seconds\":", page)
            self.assertEqual(audio, b"RIFF fake fixture")

    def test_rejects_nonblind_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            data = json.loads((root / "manifest.json").read_text()); data["prediction_included"] = True
            (root / "manifest.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "prediction-free"):
                load_package(root)

    def test_http_serves_page_audio_health_and_404(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(root))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                for path, status, marker in (("/", 200, b"blind annotation"), ("/audio.wav", 200, b"RIFF"), ("/health", 200, b"ok"), ("/missing", 404, b"not found")):
                    connection.request("GET", path); response = connection.getresponse()
                    self.assertEqual(response.status, status); self.assertIn(marker, response.read())
                connection.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
