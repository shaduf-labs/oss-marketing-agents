import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent

class ReconciliationTests(unittest.TestCase):
    def run_case(self, name):
        return subprocess.run([sys.executable, str(HERE / 'checker.py'), '--fixture', str(HERE / 'fixture.json'), '--case', name], capture_output=True, text=True)

    def test_baseline_matches_independently_written_expectation(self):
        actual = self.run_case('baseline')
        self.assertEqual(actual.returncode, 0, actual.stderr)
        expected = json.loads((HERE / 'expected-output.json').read_text())['baseline']
        self.assertEqual(json.loads(actual.stdout), expected)

    def test_unsafe_proposals_fail_closed(self):
        expected = json.loads((HERE / 'expected-output.json').read_text())
        for name in ('unsafe_global', 'unsafe_list', 'unsafe_target', 'unsafe_cutover'):
            with self.subTest(name=name):
                actual = self.run_case(name)
                self.assertEqual(actual.returncode, 2, actual.stderr)
                self.assertEqual(json.loads(actual.stdout)['classifications'], expected['baseline']['classifications'])
                self.assertEqual(json.loads(actual.stdout)['failures'], expected[name]['failures'])

    def test_case_names_are_not_silently_accepted(self):
        actual = self.run_case('missing')
        self.assertNotEqual(actual.returncode, 0)
        self.assertIn('unknown case', actual.stderr)

if __name__ == '__main__':
    unittest.main()
