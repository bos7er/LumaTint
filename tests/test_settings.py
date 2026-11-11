import json
import tempfile
import unittest
from pathlib import Path

from lumatint.profiles import ColorProfile
from lumatint.settings import load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def test_missing_file_falls_back_to_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            result = load_settings(Path(directory) / "nonexistent.json")
            self.assertFalse(result["enabled"])
            self.assertEqual(result["profile"], ColorProfile())

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "subfolder" / "settings.json"
            profile = ColorProfile(temperature=5500, brightness=93, gamma=1.05)
            save_settings(True, profile, "Custom", path)
            result = load_settings(path)
            self.assertTrue(result["enabled"])
            self.assertEqual(result["profile"], profile)
            self.assertEqual(result["preset"], "Custom")

    def test_invalid_json_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("not json", encoding="utf-8")
            self.assertFalse(load_settings(path)["enabled"])

    def test_maliciously_large_profile_values_are_clamped(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({"enabled": True, "profile": {"red": -9999, "blue": 9000}}))
            result = load_settings(path)
            self.assertEqual(result["profile"].red, 88)
            self.assertEqual(result["profile"].blue, 112)
