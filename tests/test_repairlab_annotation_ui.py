import http.client
import hashlib
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from repairlab.annotation_ui import handler_for, load_package


def package(root):
    root.mkdir(); audio = b"RIFF fake fixture"; (root / "audio.wav").write_bytes(audio)
    (root / "transcript.txt").write_text("WE FLY MOON")
    (root / "manifest.json").write_text(json.dumps({
        "format": "repairlab-blind-annotation-v1", "clip_id": "clip-a",
        "audio_sha256": hashlib.sha256(audio).hexdigest(), "prediction_included": False,
        "duration_seconds": 2.0,
        "transcript_word_count": 3,
        "selected_words": [{"word_index": 0, "word": "WE"}, {"word_index": 2, "word": "MOON"}],
    }))


class AnnotationUiTests(unittest.TestCase):
    def test_page_contains_workflow_without_model_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            page, audio = load_package(root)
            for marker in (b"RepairLab blind annotation", b"Set start", b"Set end", b"prediction_hidden", b"Download completed JSON", b"Zoom to 3 seconds", b"decodeAudioData", b"click to seek", b"Clear saved progress", b"localStorage", b"Transcript context", b"context_target_offset", b"occurrence_number", b"Occurrence"):
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

    def test_rejects_audio_that_does_not_match_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            (root / "audio.wav").write_bytes(b"RIFF replaced fixture")
            with self.assertRaisesRegex(ValueError, "audio_sha256"):
                load_package(root)

    def test_rejects_missing_or_invalid_duration(self):
        for duration in (None, 0, -1, float("inf"), True):
            with self.subTest(duration=duration), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"; package(root)
                data = json.loads((root / "manifest.json").read_text())
                if duration is None:
                    data.pop("duration_seconds")
                else:
                    data["duration_seconds"] = duration
                (root / "manifest.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, "duration_seconds"):
                    load_package(root)

    def test_rejects_malformed_or_duplicate_selected_words(self):
        cases = (
            ([{"word_index": 0, "word": "WE"}, {"word_index": 0, "word": "MOON"}], "duplicate"),
            ([{"word_index": True, "word": "WE"}], "word_index"),
            ([{"word_index": -1, "word": "WE"}], "word_index"),
            ([{"word_index": 0, "word": "  "}], "word text"),
            (["WE"], "word_index and word"),
        )
        for words, message in cases:
            with self.subTest(words=words), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"; package(root)
                data = json.loads((root / "manifest.json").read_text())
                data["selected_words"] = words
                (root / "manifest.json").write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, message):
                    load_package(root)

    def test_rejects_transcript_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            (root / "transcript.txt").write_text("WE FLY SUN")
            with self.assertRaisesRegex(ValueError, "does not match transcript"):
                load_package(root)

    def test_marks_repeated_word_occurrence_without_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "package"; package(root)
            (root / "transcript.txt").write_text("WE FLY WE")
            data = json.loads((root / "manifest.json").read_text())
            data["selected_words"][1] = {"word_index": 2, "word": "WE"}
            (root / "manifest.json").write_text(json.dumps(data))
            page, _ = load_package(root)
            self.assertIn(b'"occurrence_number":2', page)
            self.assertIn(b'"occurrence_total":2', page)

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
