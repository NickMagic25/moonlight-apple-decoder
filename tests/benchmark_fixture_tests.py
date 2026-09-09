#!/usr/bin/env python3
"""Portable fixture provenance/archival checks; payloads are synthetic bytes."""
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('compare_decoders_fixture', SCRIPTS / 'compare-decoders.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def write_fixture(directory, case):
    directory.mkdir(parents=True, exist_ok=True)
    payload = bytes(range(case['frames']))
    (directory / 'payload.bin').write_bytes(payload)
    units = [dict(frame_id=index, expected_visible_frame_id=index, expected_display_count=1,
                  pts=index, dts=index, duration=1, discontinuity=False,
                  random_access=index % case['gop'] == 0, offset=index, length=1,
                  sha256=hashlib.sha256(payload[index:index + 1]).hexdigest())
             for index in range(case['frames'])]
    manifest = dict(schema_version=1, codec=case['codec'], variant='sdr8', bit_depth=8,
                    width=case['width'], height=case['height'], chroma='420',
                    frame_rate=dict(num=case['fps'], den=1), timebase=dict(num=1, den=case['fps']),
                    payload_file='payload.bin', payload_sha256=hashlib.sha256(payload).hexdigest(),
                    access_units=units, generator=dict(pattern='moving-gradient-detail-square-frame-id-v1',
                                                       requested_bitrate_kbps=case['bitrate_kbps']))
    path = directory / 'manifest.json'
    path.write_text(json.dumps(manifest))
    return path


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mav-fixture-evidence-')
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.case = dict(name='fixture-test', width=256, height=144, fps=30, frames=4, gop=2,
                         codec='hevc', dynamic_range='sdr', bitrate_kbps=1000, fixture=None)
        self.path = write_fixture(self.root / 'source', self.case)

    def change(self, update):
        manifest = json.loads(self.path.read_text())
        update(manifest)
        self.path.write_text(json.dumps(manifest))

    def test_supported_fixture_hashes_and_measured_bitrate(self):
        info, payload = RUNNER.verify_fixture(self.path, self.case)
        self.assertEqual(info['manifest_sha256'], RUNNER.sha(self.path))
        self.assertEqual(info['payload_sha256'], RUNNER.sha(payload))
        self.assertEqual(info['measured_bitrate_kbps'], 0.24)
        self.assertEqual(info['requested_bitrate_kbps'], 1000)

    def test_missing_or_unknown_pattern_cannot_skip_pixel_identity_validation(self):
        for generator in (None, {}, dict(pattern='unverified-capture')):
            with self.subTest(generator=generator):
                self.change(lambda manifest: manifest.update(generator=generator))
                with self.assertRaisesRegex(ValueError, 'supported visible-frame-ID pattern'):
                    RUNNER.verify_fixture(self.path, self.case)

    def test_visible_identity_and_exact_gop_must_match(self):
        for field, value in [('expected_visible_frame_id', 9), ('expected_visible_frame_id', True),
                             ('expected_visible_frame_id', None), ('frame_id', 9),
                             ('random_access', True), ('expected_display_count', 0), ('pts', 0)]:
            with self.subTest(field=field, value=value):
                write_fixture(self.path.parent, self.case)
                self.change(lambda manifest: manifest['access_units'][1].update({field: value}))
                with self.assertRaisesRegex(ValueError, 'sequential one-output frames'):
                    RUNNER.verify_fixture(self.path, self.case)

    def test_stream_settings_must_match(self):
        for update in [dict(width=512), dict(height=288), dict(codec='av1'), dict(dynamic_range='hdr10'),
                       dict(fps=60), dict(frames=3), dict(bitrate_kbps=2000), dict(gop=3)]:
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    RUNNER.verify_fixture(self.path, dict(self.case, **update))

    def test_payload_integrity_and_path_confinement(self):
        for payload_file in ('../outside.bin', str(self.root / 'outside.bin'), 'escaped.bin'):
            with self.subTest(payload_file=payload_file):
                (self.root / 'outside.bin').write_bytes(bytes(range(4)))
                escaped = self.path.parent / 'escaped.bin'
                if not escaped.exists():
                    escaped.symlink_to(self.root / 'outside.bin')
                self.change(lambda manifest: manifest.update(payload_file=payload_file))
                with self.assertRaisesRegex(ValueError, 'inside its manifest directory'):
                    RUNNER.verify_fixture(self.path, self.case)
        write_fixture(self.path.parent, self.case)
        (self.path.parent / 'payload.bin').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'payload hash mismatch'):
            RUNNER.verify_fixture(self.path, self.case)

    def test_cache_identity_includes_encoder_and_all_stream_settings(self):
        build, out = self.root / 'build', self.root / 'results'
        build.mkdir()
        out.mkdir()
        binary = build / 'mav-fixture'
        binary.write_bytes(b'encoder-one')

        def generate(command, log, timeout):
            option = lambda name: command[command.index(name) + 1]
            case = dict(self.case, bitrate_kbps=int(option('--bitrate-kbps')), gop=int(option('--gop')))
            write_fixture(pathlib.Path(option('--output')), case)
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(RUNNER, 'ROOT', self.root), \
                mock.patch.object(RUNNER, 'run_encoder', side_effect=generate) as encoder:
            def prepare(case):
                return RUNNER.prepare_fixture(case, build, self.root / 'unused-aomenc', out, 180)
            first = prepare(self.case)
            cached = prepare(self.case)
            self.assertEqual(encoder.call_count, 1)
            self.assertEqual(first['original_manifest'], cached['original_manifest'])
            bitrate = prepare(dict(self.case, bitrate_kbps=2000))
            gop = prepare(dict(self.case, gop=3))
            binary.write_bytes(b'encoder-two')
            changed_encoder = prepare(self.case)
            self.assertEqual(encoder.call_count, 4)
            self.assertEqual(len({item['original_manifest'] for item in (first, bitrate, gop, changed_encoder)}), 4)
            self.assertIsNone(cached['generation_command'])
            archived, _ = RUNNER.verify_fixture(out / cached['manifest'], self.case)
            self.assertEqual(archived['manifest_sha256'], cached['manifest_sha256'])

    def test_archive_changes_cannot_report_a_passing_comparison(self):
        info, _ = RUNNER.verify_fixture(self.path, self.case)
        case = dict(self.case, fixture_info=dict(info, manifest=str(self.path.relative_to(self.root))))
        config = dict(run=dict(repetitions=1), thresholds=dict(decoded_fps_ratio=.99,
                      latency_relative_pct=5, latency_absolute_ms=.1))
        plan = dict(config=config, cases=[case], builds={'candidate': {}}, state='FINISHED',
                    runs=[dict(case=case['name'], phase=phase, setting='candidate', repetition=1)
                          for phase in ('correctness', 'timed')])

        def passed(record, *unused):
            return dict(record, passed=True, errors=[], thermal_nominal=True)

        with mock.patch.object(RUNNER, 'inspect_run', side_effect=passed), \
                mock.patch.object(RUNNER, 'report_markdown'):
            self.assertEqual(RUNNER.analyze(plan, self.root)['status'], 'PASS')
            self.change(lambda manifest: manifest['generator'].update(encoder='changed-metadata'))
            result = RUNNER.analyze(plan, self.root)
            self.assertEqual(result['cases'][0]['status'], 'INCOMPLETE')
            self.assertIn('changed after preparation', ' '.join(result['cases'][0]['issues']))
            self.path.unlink()
            self.assertEqual(RUNNER.analyze(plan, self.root)['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
