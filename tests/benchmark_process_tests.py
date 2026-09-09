#!/usr/bin/env python3
"""Fixture timeout cleanup uses only tiny Python child processes, never codecs."""
import importlib.util
import os
import pathlib
import select
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('compare_decoders_process', SCRIPTS / 'compare-decoders.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


@unittest.skipUnless(os.name == 'posix', 'process-group cleanup requires POSIX')
class EncoderProcessTests(unittest.TestCase):
    def test_exit_code_and_combined_log(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'encoder.log'
            with path.open('w') as log:
                result = RUNNER.run_encoder([sys.executable, '-c',
                    'import sys; print("stdout"); print("stderr",file=sys.stderr); sys.exit(7)'],
                    log, timeout=2)
            self.assertEqual(result.returncode, 7)
            self.assertIn('stdout', path.read_text())
            self.assertIn('stderr', path.read_text())

    def test_timeout_kills_encoder_descendant_and_reaps_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            read_fd, write_fd = os.pipe()
            child = f'import os,time; os.write({write_fd}, b"child-ready"); time.sleep(60)'
            parent = ('import subprocess,sys,time; '
                      f'subprocess.Popen([sys.executable,"-c",{child!r}],pass_fds=({write_fd},)); time.sleep(60)')
            created = []
            original = subprocess.Popen

            def spawn(*args, **kwargs):
                kwargs['pass_fds'] = (write_fd,)
                process = original(*args, **kwargs)
                created.append(process)
                os.close(write_fd)
                return process

            try:
                with mock.patch.object(RUNNER.subprocess, 'Popen', side_effect=spawn), \
                        (root / 'encoder.log').open('w') as log:
                    with self.assertRaises(subprocess.TimeoutExpired):
                        RUNNER.run_encoder([sys.executable, '-c', parent], log, timeout=0.5)
                self.assertEqual(created[0].returncode, -signal.SIGKILL)
                self.assertTrue(select.select([read_fd], [], [], 1)[0])
                self.assertEqual(os.read(read_fd, 1024), b'child-ready',
                                 'encoder descendant did not start before timeout')
                # The sleeping descendant keeps a write descriptor open. EOF
                # proves it terminated too, without relying on process-list
                # access or whether init has reaped an adopted zombie yet.
                self.assertTrue(select.select([read_fd], [], [], 1)[0],
                                'encoder descendant survived the parent timeout')
                self.assertEqual(os.read(read_fd, 1024), b'')
            finally:
                os.close(read_fd)
                if created:
                    try:
                        os.killpg(created[0].pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    created[0].wait()
                else:
                    os.close(write_fd)

    def test_interrupt_and_already_exited_group_preserve_original_exception(self):
        for exception in (KeyboardInterrupt(), subprocess.TimeoutExpired(['encoder'], 1)):
            with self.subTest(exception=type(exception).__name__):
                process = mock.Mock(pid=43210)
                process.wait.side_effect = [exception, -signal.SIGKILL]
                with mock.patch.object(RUNNER.subprocess, 'Popen', return_value=process) as spawn, \
                        mock.patch.object(RUNNER.os, 'killpg', side_effect=ProcessLookupError) as kill:
                    with self.assertRaises(type(exception)):
                        RUNNER.run_encoder(['encoder'], None, timeout=1)
                self.assertTrue(spawn.call_args.kwargs['start_new_session'])
                kill.assert_called_once_with(43210, signal.SIGKILL)
                self.assertEqual(process.wait.call_count, 2)

    def test_failed_generation_cannot_leave_a_reusable_manifest(self):
        for timed_out in (False, True):
            with self.subTest(timed_out=timed_out), tempfile.TemporaryDirectory() as directory:
                root = pathlib.Path(directory)
                build, out = root / 'build', root / 'results'
                build.mkdir()
                out.mkdir()
                (build / 'mav-fixture').write_bytes(b'fixture-generator-identity')
                case = dict(name='test', fixture=None, width=256, height=144, fps=30,
                            frames=12, gop=6, bitrate_kbps=1000, codec='hevc', dynamic_range='sdr')

                def fail(command, log, timeout):
                    target = pathlib.Path(command[command.index('--output') + 1])
                    (target / 'manifest.json').write_text('{"partial":true}')
                    if timed_out:
                        raise subprocess.TimeoutExpired(command, timeout)
                    return subprocess.CompletedProcess(command, 7)

                with mock.patch.object(RUNNER, 'ROOT', root), \
                        mock.patch.object(RUNNER, 'run_encoder', side_effect=fail):
                    with self.assertRaises(subprocess.TimeoutExpired if timed_out else ValueError):
                        RUNNER.prepare_fixture(case, build, root / 'unused-aomenc', out, 180)
                self.assertEqual(list((root / 'fixtures').rglob('manifest.json')), [])
                self.assertTrue((out / 'test-encode.log').is_file())


if __name__ == '__main__':
    unittest.main()
