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
                                                       requested_bitrate_mbps=case['bitrate_mbps']))
    path = directory / 'manifest.json'
    path.write_text(json.dumps(manifest))
    return path


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mav-fixture-evidence-')
        self.addCleanup(self.temporary.cleanup)
        self.root = pathlib.Path(self.temporary.name)
        self.case = dict(name='fixture-test', width=256, height=144, fps=30, frames=4, gop=2,
                         codec='hevc', dynamic_range='sdr', bitrate_mbps=1, fixture=None)
        self.path = write_fixture(self.root / 'source', self.case)

    def change(self, update):
        manifest = json.loads(self.path.read_text())
        update(manifest)
        self.path.write_text(json.dumps(manifest))

    def test_supported_fixture_hashes_and_measured_bitrate(self):
        info, payload = RUNNER.verify_fixture(self.path, self.case)
        self.assertEqual(info['manifest_sha256'], RUNNER.sha(self.path))
        self.assertEqual(info['payload_sha256'], RUNNER.sha(payload))
        self.assertEqual(info['measured_bitrate_mbps'], 0.00024)
        self.assertEqual(info['requested_bitrate_mbps'], 1)

    def test_legacy_fixture_kbps_are_converted_without_rewriting_evidence(self):
        for bitrate in (None, 0.001, 0.029, 50, 100, 250, 350):
            with self.subTest(bitrate=bitrate):
                case = dict(self.case, bitrate_mbps=bitrate)
                write_fixture(self.path.parent, case)
                def legacy(manifest):
                    generator = manifest['generator']
                    generator.pop('requested_bitrate_mbps')
                    generator['requested_bitrate_kbps'] = None if bitrate is None else round(bitrate * 1000)
                self.change(legacy)
                original = self.path.read_bytes()
                info, _ = RUNNER.verify_fixture(self.path, case)
                self.assertEqual(info['requested_bitrate_mbps'], bitrate)
                self.assertEqual(self.path.read_bytes(), original)

    def test_ambiguous_or_invalid_fixture_bitrate_is_rejected(self):
        for values in (dict(requested_bitrate_mbps=True), dict(requested_bitrate_mbps='1'),
                       dict(requested_bitrate_mbps=0.0001), dict(requested_bitrate_mbps=1001),
                       dict(requested_bitrate_mbps=10**1000),
                       dict(requested_bitrate_mbps=True, requested_bitrate_kbps=1000),
                       dict(requested_bitrate_kbps=1000000), dict(requested_bitrate_kbps=True),
                       dict(requested_bitrate_kbps=1000.5)):
            with self.subTest(values=values):
                write_fixture(self.path.parent, self.case)
                self.change(lambda manifest: manifest['generator'].update(values))
                with self.assertRaisesRegex(ValueError, 'bitrate'):
                    RUNNER.verify_fixture(self.path, self.case)

    def test_target_bitrates_and_fractional_mbps_reach_encoder_unchanged(self):
        build, out = self.root / 'build', self.root / 'results'
        build.mkdir()
        out.mkdir()
        (build / 'mav-fixture').write_bytes(b'encoder')
        def generate(command, log, timeout):
            value = command[command.index('--bitrate-mbps') + 1]
            self.assertNotIn('--bitrate-kbps', command)
            case = dict(self.case, bitrate_mbps=float(value))
            write_fixture(pathlib.Path(command[command.index('--output') + 1]), case)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(RUNNER, 'ROOT', self.root), \
                mock.patch.object(RUNNER, 'run_encoder', side_effect=generate) as encoder:
            for value, argument in ((50, '50'), (100, '100'), (250, '250'), (350, '350'),
                                    (0.029, '0.029'), (1.001, '1.001')):
                with self.subTest(value=value):
                    info = RUNNER.prepare_fixture(dict(self.case, bitrate_mbps=value),
                                                  build, self.root / 'unused-aomenc', out, 180)
                    command = encoder.call_args.args[0]
                    self.assertEqual(command[command.index('--bitrate-mbps') + 1], argument)
                    self.assertEqual(info['requested_bitrate_mbps'], value)

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
                       dict(fps=60), dict(frames=3), dict(bitrate_mbps=2), dict(gop=3)]:
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
            case = dict(self.case, bitrate_mbps=float(option('--bitrate-mbps')), gop=int(option('--gop')))
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
            bitrate = prepare(dict(self.case, bitrate_mbps=2))
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
                      latency_relative_pct=5, latency_absolute_ms=.1, bitrate_tolerance_pct=100))
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
