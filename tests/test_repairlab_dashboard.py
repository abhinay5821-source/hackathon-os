import base64
import http.client
import json
import math
import struct
import tempfile
import threading
import unittest
import wave
from http.server import ThreadingHTTPServer
from pathlib import Path

from repairlab.dashboard import DashboardHandler, HTML, MAX_REQUEST_BYTES, analyze_request


def wav_bytes(samples):
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "audio.wav"
        with wave.open(str(path), "wb") as audio:
            audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(16000)
            audio.writeframes(struct.pack("<" + "h" * len(samples), *samples))
        return path.read_bytes()


class DashboardTests(unittest.TestCase):
    def payload(self):
        rate = 16000
        samples = [round(7000 * math.sin(2 * math.pi * 180 * i / rate)) for i in range(rate)]
        words = [{"word": f"W{i}", "start_seconds": 0.05 + i * 0.18,
                  "end_seconds": 0.18 + i * 0.18} for i in range(5)]
        encoded = base64.b64encode(wav_bytes(samples)).decode()
        return {"baseline_audio_base64": encoded, "participant_audio_base64": encoded,
                "baseline_alignment": {"words": words},
                "participant_alignment": {"words": words}, "threshold": 2.5}

    def test_request_returns_strict_analysis_without_persisting_audio(self):
        result = analyze_request(self.payload())
        self.assertEqual(result["schema"], "repairlab-pair-analysis-v1")
        self.assertEqual(result["comparison"]["regions"], [])
        json.dumps(result, allow_nan=False)

    def test_rejects_bad_base64_and_threshold(self):
        payload = self.payload(); payload["baseline_audio_base64"] = "***"
        with self.assertRaisesRegex(ValueError, "valid base64"):
            analyze_request(payload)
        payload = self.payload(); payload["threshold"] = True
        with self.assertRaisesRegex(ValueError, "numeric"):
            analyze_request(payload)

    def test_dashboard_has_uploads_overlay_regions_and_uncertainty(self):
        for marker in ("Baseline WAV", "Participant WAV", "Energy overlay",
                       "Flagged regions", "Uncertainty", "fetch('/analyze'"):
            self.assertIn(marker, HTML)
        self.assertGreater(MAX_REQUEST_BYTES, 4 * 1024 * 1024)

    def test_http_page_and_analysis_route(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/")
            page = connection.getresponse()
            self.assertEqual(page.status, 200)
            self.assertIn(b"RepairLab review", page.read())
            body = json.dumps(self.payload()).encode()
            connection.request("POST", "/analyze", body,
                               {"Content-Type": "application/json", "Content-Length": str(len(body))})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            result = json.loads(response.read())
            self.assertEqual(result["schema"], "repairlab-pair-analysis-v1")
            connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
