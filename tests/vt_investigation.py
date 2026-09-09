#!/usr/bin/env python3
"""Synthetic accounting and trace-boundary tests; no hardware performance claims."""
import copy
import csv
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('investigate_vt', SCRIPTS / 'investigate-vt.py')
VT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VT)


def synthetic():
    rows = []
    for frame in range(8):
        start = 10000 + frame * 1000
        rows.append(dict(frame_id=frame, generation=1 if frame < 5 else 2, status=0, result=0,
            trace_valid=31, internal_samples=1, displayed_outputs=1, show_existing=0,
            scheduled_arrival_ns=start, admission_ns=start+10, preparation_start_ns=start+10,
            preparation_end_ns=start+20, vt_submit_ns=start+30, vt_return_ns=start+60,
            callback_ns=start+130+frame, handoff_ns=start+135+frame, sink_entry_ns=start+140+frame,
            hardware=1, bit_depth=8, pixel_format=875704438))
    manifest = dict(codec='av1', variant='sdr8', width=3840, height=2160, bit_depth=8, chroma='420',
                    payload_sha256='fixture', access_units=[dict(frame_id=i, random_access=i == 0,
                                                                length=100 if i == 0 else 10)
                                                          for i in range(4)])
    result = dict(status='PASS', hardware_validated=1, pixel_format=875704438,
        mode='paced', loops=2, warmup_frames=2, inflight=2, loop_mode='continuous',
        fixture_sha256='fixture', **{f: 8 for f in VT.TOTAL_FIELDS}, **{f: 0 for f in VT.ZERO_FIELDS},
        **{f: manifest[f] for f in ('codec', 'variant', 'width', 'height', 'bit_depth', 'chroma')})
    update_metrics(rows, result)
    return rows, result, manifest


def update_metrics(rows, result):
    first = {}
    for row in rows:
        if row['status'] == 0 and row['displayed_outputs'] == 1:
            first[row['generation']] = min(first.get(row['generation'], row['frame_id']), row['frame_id'])
    steady = [r for r in rows if r['status'] == 0 and r['displayed_outputs'] == 1
              and r['frame_id'] >= result['warmup_frames'] and r['frame_id'] != first[r['generation']]]
    for metric, (end, start, mask) in VT.PHASES.items():
        result[metric] = VT.distribution([r[end]-r[start] for r in steady
                                         if r['trace_valid'] & mask == mask and r[end] >= r[start]])


class TraceTests(unittest.TestCase):
    def test_warmup_and_first_successful_output_each_generation_are_excluded(self):
        rows, result, manifest = synthetic()
        phases = VT.analyze_trace(rows, result, manifest)
        self.assertEqual(phases['steady_rows'], 5)  # IDs 2,3,4,6,7; generation-2 ID 5 is cold.
        self.assertEqual(phases['metrics']['vt_submit_to_callback_ns']['count'], 5)
        self.assertEqual(phases['by_picture']['random_access']['rows'], 1)
        self.assertEqual(phases['by_picture']['inter']['rows'], 4)
        self.assertEqual(phases['errors'], [])

    def test_inline_callback_is_not_negative_after_return_time(self):
        rows, result, manifest = synthetic()
        rows[3]['vt_return_ns'] = rows[3]['callback_ns'] + 25
        update_metrics(rows, result)
        phases = VT.analyze_trace(rows, result, manifest)
        self.assertEqual(phases['callback_before_return_rows'], 1)
        self.assertEqual(phases['metrics']['submission_call_ns']['count'], 5)
        self.assertEqual(phases['metrics']['vt_return_to_callback_ns']['count'], 4)
        self.assertGreaterEqual(phases['metrics']['vt_return_to_callback_ns']['min'], 0)
        self.assertEqual(phases['errors'], [])

    def test_missing_and_invalid_returns_are_reported_separately(self):
        rows, result, manifest = synthetic()
        rows[3]['trace_valid'] &= ~4
        rows[4]['vt_return_ns'] = rows[4]['vt_submit_ns'] - 1
        update_metrics(rows, result)
        phases = VT.analyze_trace(rows, result, manifest)
        self.assertEqual(phases['missing_or_invalid_return_rows'], 2)
        self.assertEqual(phases['metrics']['submission_call_ns']['count'], 3)
        self.assertEqual(phases['metrics']['vt_return_to_callback_ns']['count'], 3)
        # An invalid return before submit must not create a plausible after-return interval.

    def test_no_steady_population_cannot_be_latency_success(self):
        rows, result, manifest = synthetic()
        result['warmup_frames'] = len(rows)
        update_metrics(rows, result)
        phases = VT.analyze_trace(rows, result, manifest)
        self.assertEqual(phases['metrics']['vt_submit_to_callback_ns']['count'], 0)
        self.assertIsNone(phases['metrics']['vt_submit_to_callback_ns']['median'])
        self.assertTrue(phases['errors'])

    def test_unreported_steady_trace_loss_is_detected(self):
        rows, result, manifest = synthetic()
        rows[3]['trace_valid'] &= ~8
        phases = VT.analyze_trace(rows, result, manifest)
        self.assertTrue(any('incomplete' in e for e in phases['errors']))

    def test_reported_percentiles_are_reproduced(self):
        rows, result, manifest = synthetic()
        result['vt_submit_to_callback_ns']['p95'] += 10
        self.assertTrue(VT.analyze_trace(rows, result, manifest)['errors'])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mav-vt-evidence-')
        self.directory = pathlib.Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.rows, self.result, manifest = synthetic()
        self.fixture = dict(document=manifest, payload_sha256='fixture')
        self.invocation = dict(case='4k-av1-sdr', variant='baseline', mode='paced', repetition=1,
            expected_frames=8, loops=2, warmup_frames=2, inflight=2, exit_code=0,
            result_file='run.json', csv_file='run.csv', artifact_sha256={})

    def save(self):
        VT.write_json(self.directory / 'run.json', self.result)
        with (self.directory / 'run.csv').open('w', newline='') as out:
            writer = csv.DictWriter(out, fieldnames=self.rows[0].keys())
            writer.writeheader()
            writer.writerows(self.rows)
        self.invocation['artifact_sha256'] = {name: VT.digest(self.directory / name)
                                              for name in ('run.json', 'run.csv')}

    def inspect(self):
        self.save()
        return VT.analyze_run(self.directory, self.invocation, self.fixture)

    def test_complete_hardware_outputs_qualify(self):
        result = self.inspect()
        self.assertTrue(result['qualified'], result['errors'])

    def test_failed_accounting_never_qualifies(self):
        for field in (*VT.ZERO_FIELDS, *VT.TOTAL_FIELDS, 'hardware_validated'):
            with self.subTest(field=field):
                original = self.result[field]
                self.result[field] = 1 if field in VT.ZERO_FIELDS else original-1
                self.assertFalse(self.inspect()['qualified'])
                self.result[field] = original

    def test_failed_process_does_not_become_success_from_pass_json(self):
        self.invocation['exit_code'] = 7
        self.assertFalse(self.inspect()['qualified'])

    def test_duplicate_csv_id_is_detected_even_when_counts_match(self):
        self.rows[3]['frame_id'] = self.rows[2]['frame_id']
        self.assertFalse(self.inspect()['qualified'])

    def test_wrong_output_format_is_detected(self):
        self.rows[4]['pixel_format'] = 0
        self.assertFalse(self.inspect()['qualified'])

    def test_missing_json_and_modified_trace_remain_failed_evidence(self):
        self.save()
        (self.directory / 'run.json').unlink()
        self.assertFalse(VT.analyze_run(self.directory, self.invocation, self.fixture)['qualified'])
        self.save()
        with (self.directory / 'run.csv').open('a') as out:
            out.write('\n')
        self.assertFalse(VT.analyze_run(self.directory, self.invocation, self.fixture)['qualified'])

    def test_partial_or_failed_cohort_has_no_aggregate_speed_claim(self):
        self.save()
        summary = dict(repetitions=2, planned_runs=2, fixtures={'4k-av1-sdr': self.fixture}, runs=[self.invocation])
        VT.write_json(self.directory / 'summary.json', summary)
        evidence = VT.analyze(self.directory)
        self.assertFalse(evidence['aggregates'][0]['cohort_qualified'])
        self.assertEqual(evidence['aggregates'][0]['metrics'], {})
        second = dict(self.invocation, repetition=2, exit_code=1)
        summary['runs'].append(second)
        VT.write_json(self.directory / 'summary.json', summary)
        evidence = VT.analyze(self.directory)
        self.assertEqual(evidence['aggregates'][0]['qualified_runs'], 1)
        self.assertEqual(evidence['aggregates'][0]['metrics'], {})

    def test_reanalysis_is_offline_and_does_not_overwrite(self):
        self.save()
        VT.write_json(self.directory / 'summary.json', dict(repetitions=1, planned_runs=1,
            fixtures={'4k-av1-sdr': self.fixture}, runs=[self.invocation]))
        with mock.patch.object(VT.subprocess, 'run', side_effect=AssertionError('must not execute replay')):
            self.assertEqual(VT.main(['--analyze', str(self.directory)]), 0)
        original = (self.directory / 'reanalysis.json').read_bytes()
        with self.assertRaises(SystemExit):
            VT.main(['--analyze', str(self.directory)])
        self.assertEqual((self.directory / 'reanalysis.json').read_bytes(), original)


class InputTests(unittest.TestCase):
    def test_invalid_or_duplicate_selections(self):
        for value in ('paced,paced', '', 'all'):
            with self.assertRaises(ValueError):
                VT.selected(value, ('paced', 'throughput'), 'modes')

    def test_variant_controls_are_explicit_and_baseline_is_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = pathlib.Path(temporary) / 'variants.json'
            for value in ({'baseline': {'MAV_VT_SYNC': '1'}}, {'baseline': {}, '../escape': {}},
                          {'baseline': {}, 'x': {'PATH': '/bad'}}, {'baseline': {}, 'x': {'MAV_VT_X': True}}):
                VT.write_json(path, value)
                with self.assertRaises(ValueError):
                    VT.variants_from(path)
            valid = {'baseline': {}, 'activity': {'MAV_VT_ACTIVITY': 'latency-critical'}}
            VT.write_json(path, valid)
            self.assertEqual(VT.variants_from(path), valid)


if __name__ == '__main__':
    unittest.main()
