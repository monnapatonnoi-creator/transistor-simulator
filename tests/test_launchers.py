"""Regression tests for the checked-in one-click launchers."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHERS = ("run_web.ps1", "เปิดเว็บ.vbs")


class TestLaunchers(unittest.TestCase):
    def test_launchers_have_no_personal_absolute_path(self):
        for name in LAUNCHERS:
            text = (ROOT / name).read_text(encoding="utf-8-sig")
            with self.subTest(name=name):
                self.assertNotIn("b6829162", text)
                self.assertNotIn("Default Project", text)

    def test_launchers_resolve_their_own_directory(self):
        ps1 = (ROOT / "run_web.ps1").read_text(encoding="utf-8-sig")
        vbs = (ROOT / "เปิดเว็บ.vbs").read_text(encoding="utf-8-sig")
        self.assertIn("$PSScriptRoot", ps1)
        self.assertIn("WScript.ScriptFullName", vbs)


if __name__ == "__main__":
    unittest.main()
