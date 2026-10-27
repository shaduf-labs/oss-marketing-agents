"""Compare checker output against an independently authored result file."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / "expected-results.json").read_text())


class FixtureTest(unittest.TestCase):
    def test_all_predeclared_cases(self):
        for case, expected in EXPECTED.items():
            with self.subTest(case=case):
                completed = subprocess.run(
                    [sys.executable, str(HERE / "checker.py"), "--case", case],
                    capture_output=True, text=True, check=False,
                )
                actual = json.loads(completed.stdout)
                self.assertEqual({key: actual[key] for key in ("pass", "issues")}, expected)
                self.assertEqual(completed.returncode, 0 if expected["pass"] else 2)
                self.assertEqual(completed.stderr, "")

    def test_unknown_case_fails_closed(self):
        completed = subprocess.run(
            [sys.executable, str(HERE / "checker.py"), "--case", "not-declared"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(json.loads(completed.stdout)["issues"], ["fixture_error"])


if __name__ == "__main__":
    unittest.main()
