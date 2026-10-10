import unittest

from repairlab.fetch_vctk_subset import member_names


class VctkSubsetTests(unittest.TestCase):
    def test_builds_transcript_and_mic1_members(self):
        self.assertEqual(
            member_names(["p225", "p226"], "001"),
            [
                "txt/p225/p225_001.txt",
                "wav48_silence_trimmed/p225/p225_001_mic1.flac",
                "txt/p226/p226_001.txt",
                "wav48_silence_trimmed/p226/p226_001_mic1.flac",
            ],
        )

    def test_rejects_malformed_or_oversized_requests(self):
        for speakers, text_id in (([], "001"), (["../bad"], "001"), (["p225"], "1"), (["p225", "p225"], "001")):
            with self.assertRaises(ValueError):
                member_names(speakers, text_id)
        with self.assertRaises(ValueError):
            member_names([f"p{number:03d}" for number in range(11)], "001")
