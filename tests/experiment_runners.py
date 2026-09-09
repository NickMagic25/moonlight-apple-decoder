#!/usr/bin/env python3
"""Portable runner accounting regressions; every subprocess and capture is mocked."""
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))


def load_runner(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), SCRIPTS / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNERS = [load_runner(name) for name in ('experiment-matrix', 'experiment-encoder')]
PASS = json.dumps(dict(status='PASS', offered=120, displayed_outputs=120,
                       vt_submit_to_callback_ns=dict(count=1, median=1000000))).encode()
FAIL = json.dumps(dict(status='FAIL', reason='synthetic failure',
                       vt_submit_to_callback_ns=None)).encode()


class RunnerTests(unittest.TestCase):
    def exercise(self, runner, first_output=PASS, first_exit=0, phase='timed'):
        with tempfile.TemporaryDirectory(prefix='mav-runner-test-') as temporary:
            root = pathlib.Path(temporary)
            binary_bytes = b'synthetic binary: subprocess execution is mocked'
            for source in (root, root / 'build-experiments/wt-parser-state'):
                binary = source / 'build/mav-replay'
                binary.parent.mkdir(parents=True)
                binary.write_bytes(binary_bytes)
            manifest = root / 'fixtures/generated/av1-sdr8-1920x1080p120-120/manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps(dict(payload_sha256='0' * 64,
                                                access_units=[{}] * 120,
                                                frame_rate=dict(num=120, den=1))))
            plan = root / 'plan.json'
            plan.write_text(json.dumps(dict(commands=[dict(case='1080-av1-sdr',
                                                          tile_columns_log2=columns,
                                                          fixture=str(manifest)) for columns in (0, 1)])))
            results = root / 'results'
            summary_path = results / 'summary.json'
            argv = [runner.__name__, '--phase', phase, '--results-dir', str(results),
                    '--repetitions', '2', '--seconds', '4']
            if runner.__name__ == 'experiment_matrix':
                argv += ['--cases', '1080-av1-sdr', '--settings', 'baseline,parser-state']
                settings = ('baseline', 'parser-state')
            else:
                argv += ['--plan', str(plan)]
                settings = ('columns0', 'columns1')
            commands, parses = [], []

            def capture(source, build, output):
                return dict(build_type='Release', binaries={
                    'mav-replay': hashlib.sha256(binary_bytes).hexdigest()})

            def invoke(command, **kwargs):
                # All earlier attempts must already be durable before the next run.
                self.assertEqual(len(json.loads(summary_path.read_text())['runs']), len(commands))
                prefix = pathlib.Path(command[command.index('--output') + 1])
                contents = first_output if not commands else PASS
                if contents is not None:
                    prefix.with_suffix('.json').write_bytes(contents)
                commands.append(command)
                return subprocess.CompletedProcess(command, first_exit if len(commands) == 1 else 0)

            original_read = runner.read_result

            def read_result(path):
                # The current completed invocation must be saved even before parsing starts.
                saved = json.loads(summary_path.read_text())['runs']
                self.assertEqual(len(saved), len(commands))
                self.assertEqual(saved[-1]['command'], commands[-1])
                self.assertEqual(saved[-1]['result_file'], str(path))
                self.assertEqual(saved[-1]['exit_code'], first_exit if len(commands) == 1 else 0)
                parses.append(path)
                return original_read(path)

            error = None
            code = None
            with mock.patch.object(runner, 'ROOT', root), \
                 mock.patch.object(runner, 'capture', side_effect=capture), \
                 mock.patch.object(runner.subprocess, 'run', side_effect=invoke), \
                 mock.patch.object(runner, 'read_result', side_effect=read_result), \
                 mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(io.StringIO()):
                try:
                    code = runner.main()
                except RuntimeError as exception:
                    error = str(exception)
            summary = json.loads(summary_path.read_text())
            self.assertEqual(len(parses), len(commands))
            first_file = pathlib.Path(summary['runs'][0]['result_file'])
            if first_output is None:
                self.assertFalse(first_file.exists())
            else:
                self.assertEqual(first_file.read_bytes(), first_output, 'raw evidence was modified')
            expected_order = [settings[0], settings[1], settings[1], settings[0]]
            if phase == 'correctness':
                expected_order = [settings[0]] if error else list(settings)
            self.assertEqual([run['setting'] for run in summary['runs']], expected_order)
            self.assertEqual([run['repetition'] for run in summary['runs']],
                             [1, 1, 2, 2] if phase == 'timed' else [1] * len(expected_order))
            self.assertEqual(summary['runs'][0]['exit_code'], first_exit)
            return code, error, summary

    def test_valid_results_preserve_success_and_rotation(self):
        for runner in RUNNERS:
            for phase in ('timed', 'correctness'):
                with self.subTest(runner=runner.__name__, phase=phase):
                    code, error, summary = self.exercise(runner, phase=phase)
                    self.assertEqual(code, 0)
                    self.assertIsNone(error)
                    self.assertTrue(all('result_error' not in run for run in summary['runs']))
                    self.assertTrue(all(run['result_status'] == 'PASS' for run in summary['runs']))

    def test_fail_result_with_zero_process_exit_is_failure(self):
        for runner in RUNNERS:
            for phase in ('timed', 'correctness'):
                with self.subTest(runner=runner.__name__, phase=phase):
                    code, error, summary = self.exercise(runner, first_output=FAIL, phase=phase)
                    first = summary['runs'][0]
                    self.assertEqual(first['exit_code'], 0)
                    self.assertEqual(first['result_status'], 'FAIL')
                    self.assertNotIn('result_error', first)
                    if phase == 'timed':
                        self.assertEqual(code, 1)
                        self.assertIsNone(error)
                        self.assertTrue(all(run['result_status'] == 'PASS' for run in summary['runs'][1:]))
                    else:
                        self.assertIsNone(code)
                        self.assertIn('correctness failed:', error)
                        self.assertEqual(len(summary['runs']), 1)

    def test_invalid_results_preserved_then_timed_runs_continue(self):
        invalid = [None, b'{"status":', b'[]', b'null', b'\xff', b'{}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":1}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":"bad"}}',
                   b'{"status":"PASS","vt_submit_to_callback_ns":{"median":NaN}}']
        for runner in RUNNERS:
            for output in invalid:
                with self.subTest(runner=runner.__name__, output=output):
                    code, error, summary = self.exercise(runner, first_output=output)
                    self.assertEqual(code, 1)
                    self.assertIsNone(error)
                    first = summary['runs'][0]
                    self.assertEqual(first['result_status'], 'MISSING_OR_INVALID_RESULT')
                    self.assertTrue(first['result_error'])
                    self.assertTrue(all('result_error' not in run for run in summary['runs'][1:]))

    def test_invalid_correctness_result_is_saved_before_failure(self):
        for runner in RUNNERS:
            with self.subTest(runner=runner.__name__):
                code, error, summary = self.exercise(runner, first_output=b'{', phase='correctness')
                self.assertIsNone(code)
                self.assertIn('correctness failed:', error)
                self.assertEqual(len(summary['runs']), 1)
                self.assertEqual(summary['runs'][0]['result_status'], 'MISSING_OR_INVALID_RESULT')

    def test_nonzero_process_exit_preserved(self):
        for runner in RUNNERS:
            for phase in ('timed', 'correctness'):
                for output in (FAIL, b'{'):
                    with self.subTest(runner=runner.__name__, phase=phase, output=output):
                        code, error, summary = self.exercise(runner, first_output=output,
                                                             first_exit=7, phase=phase)
                        self.assertEqual(summary['runs'][0]['exit_code'], 7)
                        if phase == 'timed':
                            self.assertEqual(code, 1)
                            self.assertIsNone(error)
                        else:
                            self.assertIsNone(code)
                            self.assertIn('correctness failed:', error)


if __name__ == '__main__':
    unittest.main()
