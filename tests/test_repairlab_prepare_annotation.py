import json
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path


from repairlab.prepare_annotation import prepare_package


def wav(path):
    with wave.open(str(path), "wb") as audio:
        audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        audio.writeframes(b"\x00\x00" * 16000)


class PrepareAnnotationTests(unittest.TestCase):
    def test_package_spans_transcript_and_contains_no_predictions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); audio = root / "clip.wav"; wav(audio)
            out = root / "package"
            result = prepare_package(audio, "one two three four five six seven eight nine", out, "clip-a", 5)
            self.assertEqual([x["word_index"] for x in result["selected_words"]], [0, 2, 4, 6, 8])
            self.assertEqual((out / "audio.wav").read_bytes(), audio.read_bytes())
            template = json.loads((out / "labels-template.json").read_text())
            self.assertTrue(template["prediction_hidden"])
            combined = (out / "manifest.json").read_text() + (out / "labels-template.json").read_text()
            for forbidden in ('"prediction"', '"alignment"', 'model_path'):
                self.assertNotIn(forbidden, combined)

    def test_rejects_existing_output_bad_id_and_too_many_words(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); audio = root / "clip.wav"; wav(audio)
            with self.assertRaisesRegex(ValueError, "clip_id"):
                prepare_package(audio, "one two three", root / "a", "../bad", 3)
            with self.assertRaisesRegex(ValueError, "exceed"):
                prepare_package(audio, "one two three", root / "b", "good", 4)
            (root / "c").mkdir()
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare_package(audio, "one two three", root / "c", "good", 3)

    def test_cli_outputs_strict_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); audio = root / "clip.wav"; wav(audio)
            transcript = root / "transcript.txt"
            transcript.write_text("one two three four five six")
            run = subprocess.run([sys.executable, "-m", "repairlab.prepare_annotation",
                                  str(audio), str(transcript), str(root / "package"),
                                  "--clip-id", "clip-a", "--sample-count", "3"],
                                 check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(run.stdout)["selected_words"], 3)


if __name__ == "__main__":
    unittest.main()
