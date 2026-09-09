"""Portable tests of complete software-reference evidence; no native decoding."""

import copy
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import benchmark_reference as reference


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mav-reference-test-')
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name).resolve()
        self.out = self.root / 'results'
        self.fixture = self.out / 'fixtures' / 'test'
        self.fixture.mkdir(parents=True)
        self.tool = self.root / 'build' / 'mav-reference-decode'
        self.tool.parent.mkdir()
        self.tool.write_bytes(b'fake executable; tests never execute it')
        self.tool.chmod(0o755)
        self.case = dict(name='test', width=4, height=2, frames=2, codec='hevc', dynamic_range='sdr')
        self.manifest = self.fixture / 'manifest.json'
        self.write_fixture()
        self.environment = mock.patch.dict(os.environ, {'DYLD_LIBRARY_PATH': ''})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def write_fixture(self):
        payload = self.fixture / 'payload.bin'
        payload.write_bytes(b'12')
        self.manifest.write_text(json.dumps(dict(
            width=self.case['width'], height=self.case['height'], codec=self.case['codec'],
            bit_depth=10 if self.case['dynamic_range'] == 'hdr10' else 8, chroma='420',
            payload_file='payload.bin', payload_sha256=sha(payload),
            access_units=[dict(expected_display_count=1)] * self.case['frames'],
            generator=dict(pattern=reference.REFERENCE_PATTERN))))

    def helper(self, command, log, timeout, change=None, size_delta=0):
        self.assertEqual(timeout, 7)
        self.assertEqual(command[command.index('--fixture') + 1], str(self.manifest.resolve()))
        raw = pathlib.Path(command[command.index('--output') + 1])
        expected = self.case['width'] * self.case['height'] * 3 // 2 * self.case['frames']
        hdr = self.case['dynamic_range'] == 'hdr10'
        raw.write_bytes(bytes(expected * (2 if hdr else 1) + size_delta))
        metadata = dict(status='PASS', codec=self.case['codec'], outputs=self.case['frames'],
                        decoder='libdav1d' if self.case['codec'] == 'av1' else 'hevc',
                        packing='yuv420p10le-low-bits' if hdr else 'yuv420p', row_padding='omitted',
                        fixture_sha256=sha(self.fixture / 'payload.bin'), ffmpeg_version='test-version')
        if change:
            change(metadata)
        raw.with_name(raw.name + '.json').write_text(json.dumps(metadata))
        log.write('software decode test log\n')
        return subprocess.CompletedProcess(command, 0)

    def prepare(self, callback=None):
        return reference.prepare_reference(self.tool, self.manifest, self.case, self.out, 7,
                                           callback or self.helper)

    def test_requires_reference_only_for_supported_noise_or_reference_profile(self):
        self.assertTrue(reference.requires_reference(dict(content_profile='seeded-noise-frame-id-v1')))
        self.assertTrue(reference.requires_reference(dict(pattern=reference.REFERENCE_PATTERN)))
        for value in (None, [], {}, dict(pattern=reference.SOURCE_PATTERN), dict(content_profile='other')):
            self.assertFalse(reference.requires_reference(value))

    def test_complete_sdr_reference_and_archival_after_raw_cleanup(self):
        info = self.prepare()
        self.assertEqual(info['raw_bytes'], 24)
        self.assertEqual(info['expected_samples'], 24)
        self.assertEqual(info['expected_outputs'], 2)
        self.assertEqual(info['fixture_manifest_sha256'], sha(self.manifest))
        self.assertEqual(info['raw_sha256'], sha(self.out / info['raw_path']))
        self.assertEqual(reference.validate_reference(info, self.case, self.out, require_raw=True), info)
        reference.cleanup_reference(info, self.out)
        reference.cleanup_reference(info, self.out)  # Cleanup is idempotent.
        self.assertFalse((self.out / info['raw_path']).exists())
        reference.validate_reference(info, self.case, self.out)
        with self.assertRaisesRegex(ValueError, 'raw bytes missing'):
            reference.validate_reference(info, self.case, self.out, require_raw=True)
        self.assertTrue((self.out / info['metadata_path']).is_file())
        self.assertTrue((self.out / info['command_path']).is_file())

    def test_hdr_reference_is_two_bytes_per_sample(self):
        self.case.update(codec='av1', dynamic_range='hdr10')
        self.write_fixture()
        info = self.prepare()
        self.assertEqual(info['raw_bytes'], 48)
        self.assertEqual(info['expected_samples'], 24)
        self.assertEqual(info['packing'], 'yuv420p10le-low-bits')
        self.assertEqual(info['metadata']['decoder'], 'libdav1d')

    def test_invalid_sidecars_never_leave_raw_reference(self):
        mutations = [dict(status='FAIL'), dict(codec='av1'), dict(outputs=1), dict(outputs=True),
                     dict(decoder='hevc_videotoolbox'), dict(packing='nv12'), dict(row_padding='included'),
                     dict(fixture_sha256='0' * 64), dict(ffmpeg_version='')]
        for index, mutation in enumerate(mutations):
            with self.subTest(mutation=mutation):
                self.case['name'] = 'invalid-' + str(index)
                def helper(command, log, timeout):
                    return self.helper(command, log, timeout, lambda metadata: metadata.update(mutation))
                with self.assertRaisesRegex(ValueError, 'helper metadata'):
                    self.prepare(helper)
                self.assertFalse((self.out / 'reference' / (self.case['name'] + '.yuv')).exists())
                self.assertTrue((self.out / 'reference' / (self.case['name'] + '.yuv.json')).exists())

    def test_short_and_overlong_raw_output_are_rejected(self):
        for delta in (-1, 1):
            self.case['name'] = 'size-' + str(delta)
            with self.assertRaisesRegex(ValueError, 'raw output size'):
                self.prepare(lambda command, log, timeout: self.helper(command, log, timeout, size_delta=delta))
            self.assertFalse((self.out / 'reference' / (self.case['name'] + '.yuv')).exists())

    def test_timeout_and_failed_helper_clean_partial_raw_and_keep_attempt(self):
        for failure in ('timeout', 'exit'):
            self.case['name'] = failure
            def helper(command, log, timeout):
                raw = pathlib.Path(command[command.index('--output') + 1])
                raw.write_bytes(b'partial')
                log.write('partial helper output')
                if failure == 'timeout':
                    raise subprocess.TimeoutExpired(command, timeout)
                return subprocess.CompletedProcess(command, 9)
            with self.assertRaises((subprocess.TimeoutExpired, ValueError)):
                self.prepare(helper)
            self.assertFalse((self.out / 'reference' / (failure + '.yuv')).exists())
            self.assertTrue((self.out / 'reference' / (failure + '-command.json')).is_file())
            self.assertIn('partial', (self.out / 'reference' / (failure + '.log')).read_text())

    def test_missing_helper_is_clear_and_never_launched(self):
        self.tool.unlink()
        callback = mock.Mock()
        with self.assertRaisesRegex(ValueError, 'executable mav-reference-decode is missing'):
            self.prepare(callback)
        callback.assert_not_called()

    def test_stale_output_cannot_be_reused(self):
        self.prepare()
        callback = mock.Mock()
        with self.assertRaisesRegex(ValueError, 'output already exists'):
            self.prepare(callback)
        callback.assert_not_called()

    def test_tampered_archived_metadata_and_raw_fail_validation(self):
        info = self.prepare()
        metadata = self.out / info['metadata_path']
        original = metadata.read_bytes()
        metadata.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'metadata hash mismatch'):
            reference.validate_reference(info, self.case, self.out)
        metadata.write_bytes(original)
        raw = self.out / info['raw_path']
        raw.write_bytes(b'1' * info['raw_bytes'])
        with self.assertRaisesRegex(ValueError, 'raw bytes missing or hash/size mismatch'):
            reference.validate_reference(info, self.case, self.out, require_raw=True)

    def test_incomplete_sample_provenance_and_fixture_tampering_are_rejected(self):
        info = self.prepare()
        changed = dict(info, expected_samples=info['expected_samples'] - 1)
        with self.assertRaisesRegex(ValueError, 'expected sample count'):
            reference.validate_reference(changed, self.case, self.out)
        (self.fixture / 'payload.bin').write_bytes(b'21')
        with self.assertRaisesRegex(ValueError, 'fixture payload hash mismatch'):
            reference.validate_reference(info, self.case, self.out)

    def test_metadata_content_and_command_provenance_cannot_be_relabelled(self):
        info = self.prepare()
        changed = copy.deepcopy(info)
        changed['metadata']['decoder'] = 'hevc_videotoolbox'
        with self.assertRaisesRegex(ValueError, 'recorded metadata'):
            reference.validate_reference(changed, self.case, self.out)
        changed = dict(info, command=['another tool'])
        with self.assertRaisesRegex(ValueError, 'command provenance changed'):
            reference.validate_reference(changed, self.case, self.out)

    def test_paths_and_cleanup_cannot_escape_or_delete_other_artifacts(self):
        info = self.prepare()
        for path in ('../external.yuv', str(self.root / 'external.yuv')):
            with self.assertRaisesRegex(ValueError, 'artifact'):
                reference.cleanup_reference(dict(info, raw_path=path), self.out)
        with self.assertRaisesRegex(ValueError, 'unrelated artifact'):
            reference.cleanup_reference(dict(info, raw_path='fixtures/test/payload.bin'), self.out)
        self.assertEqual((self.fixture / 'payload.bin').read_bytes(), b'12')

    def test_inferred_loader_environment_is_bounded_and_recorded(self):
        libroot = self.root / 'ffmpeg'
        (libroot / 'lib').mkdir(parents=True)
        library = libroot / 'lib' / 'libavcodec.63.dylib'
        library.write_bytes(b'fake library')
        (self.tool.parent / 'CMakeCache.txt').write_text('MAV_FFMPEG_ROOT:PATH=' + str(libroot) + '\n')
        info = self.prepare()
        self.assertEqual(info['command'][:2], ['/usr/bin/env', 'DYLD_LIBRARY_PATH=' + str(libroot / 'lib')])
        self.assertEqual(info['libraries_sha256'], {str(library): sha(library)})
        self.assertEqual(os.environ['DYLD_LIBRARY_PATH'], '')

    def test_missing_metadata_cleanup_and_invalid_timeout(self):
        def helper(command, log, timeout):
            self.helper(command, log, timeout)
            pathlib.Path(command[command.index('--output') + 1] + '.json').unlink()
            return subprocess.CompletedProcess(command, 0)
        with self.assertRaisesRegex(ValueError, 'cannot read metadata'):
            self.prepare(helper)
        self.assertFalse((self.out / 'reference/test.yuv').exists())
        for timeout in (0, -1, float('inf'), float('nan'), True):
            with self.assertRaisesRegex(ValueError, 'timeout'):
                reference.prepare_reference(self.tool, self.manifest, self.case, self.out, timeout, mock.Mock())


if __name__ == '__main__':
    unittest.main()
