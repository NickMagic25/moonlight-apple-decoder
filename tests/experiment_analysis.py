#!/usr/bin/env python3
"""Portable synthetic experiment accounting tests; no decoder or CSV processing."""
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('summarize_experiments', SCRIPTS / 'summarize-experiments.py')
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


def result(status='PASS', displayed=100, median=100):
    return dict(status=status, offered=100, displayed_outputs=displayed,
                vt_submit_to_callback_ns=dict(count=90, median=median, p95=median+10,
                                              p99=median+20, mean=median))


class AnalysisTests(unittest.TestCase):
    def analyze(self, candidate, flagged=False, positive=False):
        with tempfile.TemporaryDirectory(prefix='mav-analysis-test-') as temporary:
            root = pathlib.Path(temporary)
            collection = root / 'collection'
            collection.mkdir()
            case = '1080-av1-sdr'
            invocations = []
            for repetition in range(1, 4):
                for setting in ('baseline', 'parser-state'):
                    output = collection / f'{setting}-rep{repetition}.json'
                    invocation = dict(case=case, setting=setting, repetition=repetition,
                                      exit_code=0, result_file=str(output), command=['synthetic'])
                    contents = json.dumps(result()).encode()
                    if setting == 'parser-state':
                        if positive:
                            contents = json.dumps(result(median=80)).encode()
                        elif repetition == 1:
                            contents = candidate
                            if flagged:
                                invocation.update(result_error='runner rejected output',
                                                  result_status='MISSING_OR_INVALID_RESULT')
                        elif repetition == 2:
                            contents = json.dumps(result(status='FAIL', displayed=90, median=70)).encode()
                            invocation['exit_code'] = 1
                        else:
                            # An apparent PASS from a failing process must not qualify either.
                            invocation['exit_code'] = 7
                    if contents is not None:
                        output.write_bytes(contents)
                    invocations.append(invocation)
            (collection / 'summary.json').write_text(json.dumps(dict(
                phase='timed', fixtures={case: {}}, runs=invocations)))
            output = root / 'comparison.json'
            with mock.patch.object(ANALYZER, 'ROOT', root), \
                 mock.patch.object(sys, 'argv', ['summarize-experiments', '--input', str(collection),
                                                '--output', str(output)]), \
                 mock.patch.object(ANALYZER, 'enrich', side_effect=AssertionError('unexpected trace read')), \
                 contextlib.redirect_stdout(io.StringIO()):
                ANALYZER.main()
            document = json.loads(output.read_text())
            self.assertEqual(len(document['runs']), 6)
            first_raw = collection / 'parser-state-rep1.json'
            if candidate is not None and not positive:
                self.assertEqual(first_raw.read_bytes(), candidate, 'raw evidence was modified')
            elif not positive:
                self.assertFalse(first_raw.exists())
            return document

    def assert_unknown_and_failed_totals(self, document):
        candidate = next(group for group in document['aggregates'] if group['setting'] == 'parser-state')
        self.assertEqual(candidate['runs'], 3)
        self.assertEqual(candidate['pass_runs'], 0)
        self.assertEqual(candidate['unknown_accounting_runs'], 1)
        self.assertIsNone(candidate['offered'])
        self.assertIsNone(candidate['displayed'])
        self.assertEqual(candidate['known_offered'], 200)
        self.assertEqual(candidate['known_displayed'], 190)
        self.assertEqual(candidate['qualified_passing_pairs'], 0)
        self.assertEqual(candidate['paired_changes'], {})
        # Failed run survivor timings remain diagnostic, and the failed totals are unchanged.
        self.assertEqual(candidate['metrics']['vt_submit_to_callback_ns']['per_run_medians'], [70, 100])
        attempts = [run for run in document['runs'] if run['setting'] == 'parser-state']
        self.assertEqual([run['exit_code'] for run in attempts], [0, 1, 7])
        self.assertEqual(attempts[0]['result']['status'], 'MISSING_OR_INVALID_RESULT')
        self.assertFalse(attempts[0]['result']['accounting_available'])
        self.assertTrue(attempts[0]['result']['reason'])
        self.assertEqual(attempts[1]['result']['status'], 'FAIL')
        self.assertEqual(attempts[1]['result']['displayed_outputs'], 90)
        self.assertTrue(all(not run['phases']['trace_available'] for run in attempts))
        baseline = next(group for group in document['aggregates'] if group['setting'] == 'baseline')
        self.assertEqual((baseline['pass_runs'], baseline['offered'], baseline['displayed']), (3, 300, 300))

    def test_legacy_invalid_results_do_not_hide_failed_runs(self):
        invalid = [None, b'{"status":', b'[]', b'null', b'\xff', b'{}', b'{"status":42}',
                   b'{"status":"ERROR"}', b'{"status":"PASS","vt_submit_to_callback_ns":1}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":"bad"}}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":true}}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":NaN}}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":1e10000}}']
        for contents in invalid:
            with self.subTest(contents=contents):
                self.assert_unknown_and_failed_totals(self.analyze(contents))

    def test_runner_error_is_authoritative_even_if_output_later_looks_valid(self):
        # The bogus fixture hash would invoke enrich if the recorded rejection were ignored.
        apparently_valid = json.dumps(dict(result(), fixture_sha256='untrusted')).encode()
        for contents in (None, b'{', b'[]', b'\xff', apparently_valid):
            with self.subTest(contents=contents):
                document = self.analyze(contents, flagged=True)
                self.assert_unknown_and_failed_totals(document)
                first = next(run for run in document['runs'] if run['setting'] == 'parser-state')
                self.assertEqual(first['result_error'], 'runner rejected output')
                self.assertEqual(first['result']['reason'], first['result_error'])

    def test_valid_pairs_still_compare_within_repetitions(self):
        document = self.analyze(None, positive=True)
        candidate = next(group for group in document['aggregates'] if group['setting'] == 'parser-state')
        self.assertEqual(candidate['qualified_passing_pairs'], 3)
        self.assertEqual((candidate['pass_runs'], candidate['offered'], candidate['displayed']), (3, 300, 300))
        changes = candidate['paired_changes']['vt_submit_to_callback_ns']
        self.assertEqual(changes['per_repetition_delta_ns'], [-20, -20, -20])
        self.assertEqual(changes['paired_median_delta_ns'], -20)
        self.assertAlmostEqual(changes['paired_median_change_percent'], -20)


if __name__ == '__main__':
    unittest.main()
