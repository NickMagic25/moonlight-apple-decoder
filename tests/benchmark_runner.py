#!/usr/bin/env python3
"""Portable regression tests: no native binaries or hardware are executed."""

import contextlib
import copy
import csv
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import benchmark_config
import yaml

SPEC = importlib.util.spec_from_file_location("compare_decoders", ROOT / "scripts/compare-decoders.py")
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def case_config(name="case"):
    return dict(name=name, width=320, height=180, fps=60, codec="av1", dynamic_range="sdr",
                bitrate_mbps=None, gop=60, frames=3, fixture=None,
                decoder=dict(benchmark_config.DECODER_DEFAULTS),
                fixture_info=dict(payload_sha256="0" * 64, manifest_sha256="1" * 64,
                                  manifest="fixtures/manifest.json"))


def trace_rows(vt_ns=(1000000, 2000000, 3000000)):
    rows = []
    for index, latency in enumerate(vt_ns):
        arrival = 1000000000 + index * 16666667
        rows.append(dict(frame_id=index, generation=1, status=0, result=0, trace_valid=31,
                         internal_samples=1, displayed_outputs=1, show_existing=0,
                         scheduled_arrival_ns=arrival, admission_ns=arrival + 100000,
                         preparation_start_ns=arrival + 110000, preparation_end_ns=arrival + 120000,
                         vt_submit_ns=arrival + 200000, vt_return_ns=arrival + 250000,
                         callback_ns=arrival + 200000 + latency,
                         handoff_ns=arrival + 210000 + latency,
                         sink_entry_ns=arrival + 220000 + latency,
                         hardware=1, bit_depth=8, pixel_format=875704438))
    return rows


def native_result(case, phase="timed", rows=None):
    rows = rows or trace_rows()
    return dict(status="PASS", mode="paced" if phase == "timed" else "correctness",
                codec=case["codec"], variant="sdr8", width=case["width"], height=case["height"],
                requested_fps=case["fps"], fixture_sha256=case["fixture_info"]["payload_sha256"],
                inflight=case["decoder"]["inflight"], power_requested=case["decoder"]["power"],
                consumer_retention_delay_ms=case["decoder"]["consumer_delay_ms"], bit_depth=8, chroma="420",
                offered=3, submitted=3, completed=3, displayed_outputs=3, scheduler_drops=0,
                rejected=0, failed_or_cancelled_or_dropped=0, expected_display_mismatches=0,
                trace_overflow=0, resets=0, hardware_validated=True, decoded_fps=60.0,
                warmup_frames=0, loops=1, loop_mode="continuous", run_seconds=0.05, thermal_state=0,
                steady_excludes_first_output_each_generation=True,
                correctness_sink=True, iosurface_metal_verified=True, retained_after_destroy_verified=True,
                vt_submit_to_callback_ns=RUNNER.distribution([r["callback_ns"] - r["vt_submit_ns"] for r in rows[1:]]))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mav-comparison-test-")
        self.out = pathlib.Path(self.temporary.name).resolve()
        self.case = case_config()
        self.thresholds = dict(benchmark_config.THRESHOLD_DEFAULTS)

    def tearDown(self):
        self.temporary.cleanup()

    def evidence(self, result=None, rows=None, phase="timed", setting="candidate", repetition=1):
        rows = trace_rows() if rows is None else rows
        result = native_result(self.case, phase, rows) if result is None else result
        prefix = "{}-{}-{}".format(phase, setting, repetition)
        result_path = self.out / (prefix + ".json")
        csv_path = self.out / (prefix + ".csv")
        result_path.write_text(json.dumps(result))
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=trace_rows()[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        command, _ = RUNNER.replay_command("/synthetic/mav-replay", "/fixture.json", "/out/run",
                                           self.case, dict(seconds=0.05, warmup_frames=0), phase)
        return dict(case=self.case["name"], setting=setting, phase=phase, repetition=repetition, command=command,
                    state="FINISHED", exit_code=0, expected_offered=3,
                    result_file=result_path.name, csv_file=csv_path.name,
                    result_file_sha256=RUNNER.sha(result_path), csv_file_sha256=RUNNER.sha(csv_path))

    def inspect(self, record):
        return RUNNER.inspect_run(record, self.case, self.out, self.thresholds)

    def test_valid_trace_recomputes_internal_and_public_latency(self):
        result = self.inspect(self.evidence())
        self.assertTrue(result["passed"], result["errors"])
        self.assertAlmostEqual(result["metrics"]["vt_median_ms"], 2.5)
        self.assertAlmostEqual(result["metrics"]["vt_p95_ms"], 2.95)
        self.assertAlmostEqual(result["metrics"]["public_median_ms"], 2.72)
        self.assertAlmostEqual(result["first_output_ms"], 1.22)
        self.assertTrue(result["thermal_nominal"])
        self.assertEqual(result["derived"]["public_complete_au_to_output_ns"]["count"], 2)

    def test_correctness_requires_all_hardware_sink_checks(self):
        self.assertTrue(self.inspect(self.evidence(phase="correctness"))["passed"])
        for key in ("correctness_sink", "iosurface_metal_verified", "retained_after_destroy_verified"):
            with self.subTest(key=key):
                native = native_result(self.case, "correctness")
                native[key] = False
                result = self.inspect(self.evidence(native, phase="correctness"))
                self.assertFalse(result["passed"])
                self.assertTrue(any(key in error for error in result["errors"]))

    def test_native_fail_zero_exit_and_bad_process_states_never_pass(self):
        native = native_result(self.case)
        native.update(status="FAIL", reason="synthetic dropped frame")
        result = self.inspect(self.evidence(native))
        self.assertFalse(result["passed"])
        self.assertTrue(any("native FAIL" in error for error in result["errors"]))
        for state, exit_code in (("FINISHED", 1), ("ERROR", None), ("RUNNING", None)):
            with self.subTest(state=state, exit_code=exit_code):
                record = self.evidence()
                record.update(state=state, exit_code=exit_code)
                self.assertFalse(self.inspect(record)["passed"])

    def test_missing_malformed_and_nonfinite_evidence_never_passes(self):
        contents = [None, "{", "[]", "null", "{}", '{"status":"PASS","decoded_fps":NaN}',
                    '{"status":"PASS","decoded_fps":Infinity}']
        for content in contents:
            with self.subTest(content=content):
                record = self.evidence()
                path = self.out / record["result_file"]
                if content is None:
                    path.unlink()
                    record["result_file_sha256"] = None
                else:
                    path.write_text(content)
                    record["result_file_sha256"] = RUNNER.sha(path)
                self.assertFalse(self.inspect(record)["passed"])
        for key, value in (("decoded_fps", 0), ("decoded_fps", "60"), ("offered", True),
                           ("hardware_validated", False), ("fixture_sha256", "changed"),
                           ("requested_fps", 120), ("warmup_frames", 3)):
            with self.subTest(key=key, value=value):
                native = native_result(self.case)
                native[key] = value
                self.assertFalse(self.inspect(self.evidence(native))["passed"])

    def test_hash_drift_and_malformed_csv_never_pass(self):
        for field in ("result_file", "csv_file"):
            with self.subTest(field=field):
                record = self.evidence()
                path = self.out / record[field]
                path.write_text(path.read_text() + "\n")
                checked = self.inspect(record)
                self.assertFalse(checked["passed"])
                self.assertTrue(any("changed since execution" in error for error in checked["errors"]))
        record = self.evidence()
        path = self.out / record["csv_file"]
        path.write_text("frame_id,status\n0,not-an-integer\n")
        record["csv_file_sha256"] = RUNNER.sha(path)
        self.assertFalse(self.inspect(record)["passed"])

    def test_accounting_rate_trace_identity_and_latency_summary_are_checked(self):
        for field, value in (("scheduler_drops", 1), ("rejected", 1), ("completed", 2),
                             ("displayed_outputs", 2), ("failed_or_cancelled_or_dropped", 1),
                             ("trace_overflow", 1), ("expected_display_mismatches", 1),
                             ("decoded_fps", 59.0)):
            with self.subTest(field=field):
                native = native_result(self.case)
                native[field] = value
                self.assertFalse(self.inspect(self.evidence(native))["passed"])
        native = native_result(self.case)
        native["vt_submit_to_callback_ns"]["p99"] += 100000
        checked = self.inspect(self.evidence(native))
        self.assertFalse(checked["passed"])
        self.assertIn("native VT latency summary differs from raw CSV", checked["errors"])
        rows = trace_rows()
        rows[2]["frame_id"] = 1
        self.assertFalse(self.inspect(self.evidence(rows=rows))["passed"])

    def test_successful_json_cannot_hide_bad_per_frame_trace(self):
        for key, value in (("result", -1), ("hardware", 0), ("bit_depth", 10)):
            with self.subTest(key=key):
                rows = trace_rows()
                rows[1][key] = value
                self.assertFalse(self.inspect(self.evidence(rows=rows))["passed"])
        rows = trace_rows()
        rows[0]["status"] = 4
        self.assertFalse(self.inspect(self.evidence(rows=rows, phase="correctness"))["passed"],
                         "a cancelled CSV event cannot substantiate all-success JSON accounting")

    def test_run_cannot_change_its_planned_warmup_or_loop_policy(self):
        for key, value in (("warmup_frames", 1), ("loops", 2), ("loop_mode", "reset")):
            with self.subTest(key=key):
                native = native_result(self.case)
                native[key] = value
                # Changing warmup from zero to one would otherwise leave these
                # distributions unchanged: frame zero is already a cold output.
                self.assertFalse(self.inspect(self.evidence(native))["passed"])

    def test_missing_steady_trace_cannot_be_hidden_by_recomputing_native_summary(self):
        for mutation in ("vt_bit", "public_bit", "vt_timestamp", "public_timestamp"):
            with self.subTest(mutation=mutation):
                rows = trace_rows()
                if mutation == "vt_bit":
                    rows[1]["trace_valid"] &= ~8
                elif mutation == "public_bit":
                    rows[1]["trace_valid"] &= ~16
                elif mutation == "vt_timestamp":
                    rows[1]["callback_ns"] = rows[1]["vt_submit_ns"] - 1
                else:
                    rows[1]["sink_entry_ns"] = rows[1]["scheduled_arrival_ns"] - 1
                native = native_result(self.case)
                if mutation in ("vt_bit", "vt_timestamp"):
                    native["vt_submit_to_callback_ns"] = RUNNER.distribution(
                        [rows[2]["callback_ns"] - rows[2]["vt_submit_ns"]])
                self.assertFalse(self.inspect(self.evidence(native, rows))["passed"])

    def test_replay_maps_stream_decoder_and_phase_settings_exactly(self):
        case = case_config()
        case.update(frames=120, fps=240)
        case["decoder"] = dict(inflight=3, queue_depth=32, power=0,
                               consumer_delay_ms=8, jitter_us=1000, seed=23)
        run = dict(seconds=3, warmup_frames=77)
        for phase, mode, loops, warmup, offered in (("timed", "paced", 6, 77, 720),
                                                   ("correctness", "correctness", 1, 0, 120)):
            command, count = RUNNER.replay_command("/binary with spaces/mav-replay", "/fixture with spaces.json",
                                                 "/out path/run", case, run, phase)
            self.assertEqual(command[0], "/binary with spaces/mav-replay")
            flags = dict(zip(command[1::2], command[2::2]))
            self.assertEqual(flags, {"--fixture": "/fixture with spaces.json", "--output": "/out path/run",
                                    "--mode": mode, "--fps": "240", "--loops": str(loops),
                                    "--loop-mode": "continuous", "--warmup": str(warmup), "--inflight": "3",
                                    "--queue-depth": "32", "--power": "0", "--consumer-delay-ms": "8",
                                    "--jitter-us": "1000", "--seed": "23"})
            self.assertEqual(count, offered)
            self.assertNotIn("--bitrate-mbps", command, "bitrate belongs to fixture encoding")

    def test_paired_gate_uses_run_differences_and_both_allowances(self):
        def metrics(values):
            return [{"metrics": {name: value for name in RUNNER.METRICS}} for value in values]
        thresholds = dict(self.thresholds, latency_absolute_ms=1.1)
        result = RUNNER.paired_metrics(metrics([1.0, 2.0, 100.0]), metrics([2.0, 100.0, 101.0]), thresholds)
        for metric in result.values():
            self.assertEqual(metric["paired_delta_ms"], [1.0, 98.0, 1.0])
            self.assertEqual(metric["median_paired_delta_ms"], 1.0)
            self.assertEqual(metric["candidate_median_ms"] - metric["baseline_median_ms"], 98.0)
            self.assertFalse(metric["threshold_exceeded"], "difference of medians would incorrectly fail this example")
        for baseline, candidate, exceeded in ((1.0, 1.08, False), (1.0, 1.11, True),
                                               (10.0, 10.4, False), (10.0, 10.6, True)):
            result = RUNNER.paired_metrics(metrics([baseline] * 3), metrics([candidate] * 3), self.thresholds)
            self.assertTrue(all(metric["threshold_exceeded"] == exceeded for metric in result.values()))

    def plan(self, repetitions=1, baseline=True):
        # Real archived test files exercise analysis integrity checks. Their
        # bytes are synthetic; these portable tests never invoke a native parser.
        directory = self.out / "fixtures"
        directory.mkdir(exist_ok=True)
        payload = directory / "payload.bin"
        payload.write_bytes(bytes(range(self.case["frames"])))
        manifest = dict(schema_version=1, codec=self.case["codec"], variant="sdr8", bit_depth=8,
                        width=self.case["width"], height=self.case["height"], chroma="420",
                        frame_rate=dict(num=self.case["fps"], den=1),
                        timebase=dict(num=1, den=self.case["fps"]), payload_file=payload.name,
                        payload_sha256=RUNNER.sha(payload),
                        generator=dict(pattern="moving-gradient-detail-square-frame-id-v1",
                                       requested_bitrate_mbps=self.case["bitrate_mbps"]),
                        access_units=[dict(frame_id=index, expected_visible_frame_id=index,
                                           expected_display_count=1, pts=index, dts=index, duration=1,
                                           discontinuity=False, random_access=index % self.case["gop"] == 0,
                                           offset=index, length=1)
                                      for index in range(self.case["frames"])])
        path = directory / "manifest.json"
        path.write_text(json.dumps(manifest))
        self.case["fixture_info"].update(manifest_sha256=RUNNER.sha(path),
                                         payload_sha256=RUNNER.sha(payload))
        builds = {key: dict(binary_sha256=key, environment={})
                  for key in (("baseline", "candidate") if baseline else ("candidate",))}
        runs = []
        for setting in builds:
            runs.append(self.evidence(phase="correctness", setting=setting))
            for repetition in range(1, repetitions + 1):
                runs.append(self.evidence(setting=setting, repetition=repetition))
        return dict(state="FINISHED", builds=builds, cases=[self.case], runs=runs,
                    config=dict(thresholds=self.thresholds, run=dict(repetitions=repetitions)))

    def test_analysis_baseline_failure_incomplete_and_thermal_are_not_green(self):
        plan = self.plan()
        self.assertEqual(RUNNER.analyze(plan, self.out)["cases"][0]["status"], "PASS")
        for mutation, status in (("baseline_fail", "BASELINE_FAILURE"), ("candidate_fail", "REGRESSION"),
                                 ("missing", "INCOMPLETE"), ("duplicate", "INCOMPLETE"),
                                 ("unfinished", "INCOMPLETE"), ("thermal", "INCONCLUSIVE")):
            with self.subTest(mutation=mutation):
                plan = self.plan()
                if mutation == "missing":
                    plan["runs"].pop()
                elif mutation == "duplicate":
                    plan["runs"][-1] = plan["runs"][0]
                elif mutation == "unfinished":
                    plan["state"] = "RUNNING"
                else:
                    target = "baseline" if mutation == "baseline_fail" else "candidate"
                    record = next(r for r in plan["runs"] if r["setting"] == target and r["phase"] == "timed")
                    native = native_result(self.case)
                    if mutation == "thermal":
                        native["thermal_state"] = 1
                    else:
                        native["status"] = "FAIL"
                    replacement = self.evidence(native, setting=target)
                    record.update(replacement)
                result = RUNNER.analyze(plan, self.out)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["cases"][0]["status"], status)
                self.assertTrue((self.out / "junit.xml").is_file())
                self.assertTrue((self.out / "report.md").is_file())

    def test_unexpected_run_identity_is_incomplete_even_with_matching_count(self):
        for field, value in (("phase", "unexpected"), ("repetition", 99), ("setting", "unplanned")):
            with self.subTest(field=field):
                plan = self.plan()
                plan["runs"][-1][field] = value
                result = RUNNER.analyze(plan, self.out)
                self.assertEqual(result["status"], "FAIL")
                self.assertEqual(result["cases"][0]["status"], "INCOMPLETE")

    def test_candidate_only_is_explicit_and_failed_candidate_cannot_pass(self):
        plan = self.plan(baseline=False)
        result = RUNNER.analyze(plan, self.out)
        self.assertEqual(result["comparison"], "candidate-only")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["cases"][0]["comparisons"], {})
        plan["runs"][-1]["exit_code"] = 1
        self.assertEqual(RUNNER.analyze(plan, self.out)["cases"][0]["status"], "FAIL")

    def test_markdown_and_json_agree_on_bitrate_and_failed_or_incomplete_status(self):
        for mutation in ('pass', 'baseline_fail', 'candidate_fail', 'missing_run', 'missing_fixture'):
            with self.subTest(mutation=mutation):
                self.case['bitrate_mbps'] = 350.0
                plan = self.plan()
                if mutation == 'candidate_fail':
                    plan['runs'][-1]['exit_code'] = 1
                elif mutation == 'baseline_fail':
                    plan['runs'][1]['exit_code'] = 1
                elif mutation == 'missing_run':
                    plan['runs'].pop()
                elif mutation == 'missing_fixture':
                    (self.out / self.case['fixture_info']['manifest']).unlink()
                result = RUNNER.analyze(plan, self.out)
                machine = json.loads((self.out / 'results.json').read_text())
                markdown = (self.out / 'report.md').read_text()
                self.assertEqual(machine, result)
                self.assertIn('Overall: **' + machine['status'] + '**', markdown)
                case = machine['cases'][0]
                self.assertEqual(case['status'], {'pass': 'INCONCLUSIVE',
                    'baseline_fail': 'BASELINE_FAILURE', 'candidate_fail': 'REGRESSION',
                    'missing_run': 'INCOMPLETE', 'missing_fixture': 'INCOMPLETE'}[mutation])
                self.assertIn('| case | ' + case['status'] + ' | 350.000 |', markdown)
                self.assertEqual(case['bitrate']['requested_mbps'], 350.0)
                self.assertIn('[results.json](results.json)', markdown)
                self.assertIn('Requested Mbps', markdown)
                self.assertIn('Measured Mbps', markdown)
                if mutation == 'missing_fixture':
                    self.assertIsNone(case['bitrate']['measured_mbps'])
                    self.assertIsNone(case['bitrate']['measured_to_requested_ratio'])
                else:
                    # Three payload bytes at 60 fps represent 480 bits/s.
                    self.assertEqual(case['bitrate']['measured_mbps'], 0.00048)
                    self.assertAlmostEqual(case['bitrate']['measured_to_requested_ratio'], .00048 / 350)
                if mutation == 'pass':
                    self.assertEqual(case['status'], 'INCONCLUSIVE', 'a low-bitrate stream cannot establish the requested workload')
                    self.assertFalse(case['bitrate']['coverage_passed'])
                    self.assertTrue(all(run['passed'] for run in case['runs']))
                    self.assertIn('requested bitrate coverage was not established', markdown)

    def test_legacy_plan_analysis_converts_units_without_changing_archived_inputs(self):
        for kbps in (None, 29, 50000, 350000):
            with self.subTest(kbps=kbps):
                self.case['bitrate_mbps'] = None if kbps is None else kbps / 1000
                plan = self.plan()
                case = plan['cases'][0]
                case.pop('bitrate_mbps')
                case['bitrate_kbps'] = kbps
                info = case['fixture_info']
                info['requested_bitrate_kbps'] = kbps
                info['measured_bitrate_kbps'] = .48
                fixture_path = self.out / info['manifest']
                manifest = json.loads(fixture_path.read_text())
                generator = manifest['generator']
                generator.pop('requested_bitrate_mbps')
                generator['requested_bitrate_kbps'] = kbps
                fixture_path.write_text(json.dumps(manifest))
                info['manifest_sha256'] = RUNNER.sha(fixture_path)
                plan['config']['cases'] = [copy.deepcopy(case)]
                original = copy.deepcopy(plan)
                fixture_before = fixture_path.read_bytes()
                result = RUNNER.analyze(plan, self.out)
                self.assertEqual(result['cases'][0]['status'], 'PASS' if kbps is None else 'INCONCLUSIVE')
                self.assertEqual(result['cases'][0]['bitrate']['requested_mbps'], None if kbps is None else kbps / 1000)
                self.assertNotIn('bitrate_kbps', result['config']['cases'][0])
                self.assertAlmostEqual(result['cases'][0]['settings']['fixture_info']['measured_bitrate_mbps'], .00048)
                self.assertEqual(plan, original)
                self.assertEqual(fixture_path.read_bytes(), fixture_before)
                self.case.pop('bitrate_kbps')

    def test_default_encoder_policy_has_no_fabricated_bitrate_target(self):
        result = RUNNER.analyze(self.plan(), self.out)
        self.assertEqual(result['status'], 'PASS')
        self.assertIsNone(result['cases'][0]['bitrate']['requested_mbps'])
        self.assertIsNone(result['cases'][0]['bitrate']['measured_to_requested_ratio'])
        self.assertIn('| Default |', (self.out / 'report.md').read_text())

    def test_bitrate_coverage_uses_measured_payload_and_configured_tolerance(self):
        # The synthetic fixture measures .00048 Mbps, 52% below this target.
        self.case['bitrate_mbps'] = .001
        for tolerance, status in ((20, 'INCONCLUSIVE'), (52, 'PASS'), (60, 'PASS')):
            with self.subTest(tolerance=tolerance):
                self.thresholds['bitrate_tolerance_pct'] = tolerance
                result = RUNNER.analyze(self.plan(), self.out)
                case = result['cases'][0]
                self.assertEqual(case['status'], status)
                self.assertEqual(case['bitrate']['coverage_passed'], status == 'PASS')
                self.assertEqual(case['bitrate']['tolerance_pct'], tolerance)

    def test_bitrate_tolerance_boundaries_are_inclusive_without_accepting_outside_rates(self):
        for measured, passed in ((45, True), (55, True), (50, True),
                                 (44.999999, False), (55.000001, False)):
            with self.subTest(measured=measured):
                self.assertEqual(RUNNER.bitrate_covered(50, measured, 10), passed)
        self.assertTrue(RUNNER.bitrate_covered(50, 50, 0))
        self.assertFalse(RUNNER.bitrate_covered(50, 50.000001, 0))
        self.assertIsNone(RUNNER.bitrate_covered(None, 50, 20))
        self.assertIsNone(RUNNER.bitrate_covered(50, None, 20))

    def test_bitrate_overshoot_cannot_establish_target_coverage(self):
        self.case['bitrate_mbps'] = .001
        plan = self.plan()
        info = self.case['fixture_info']
        path = self.out / info['manifest']
        manifest = json.loads(path.read_text())
        payload = path.parent / manifest['payload_file']
        payload.write_bytes(b'four' * 3)
        manifest['payload_sha256'] = RUNNER.sha(payload)
        for index, unit in enumerate(manifest['access_units']):
            unit.update(offset=4 * index, length=4)
        path.write_text(json.dumps(manifest))
        info.update(manifest_sha256=RUNNER.sha(path), payload_sha256=RUNNER.sha(payload))
        for run in plan['runs']:
            result_path = self.out / run['result_file']
            native = json.loads(result_path.read_text())
            native['fixture_sha256'] = info['payload_sha256']
            result_path.write_text(json.dumps(native))
            run['result_file_sha256'] = RUNNER.sha(result_path)
        result = RUNNER.analyze(plan, self.out)
        case = result['cases'][0]
        self.assertTrue(all(run['passed'] for run in case['runs']))
        self.assertEqual(case['bitrate']['measured_mbps'], .00192)
        self.assertEqual(case['status'], 'INCONCLUSIVE')
        self.assertFalse(case['bitrate']['coverage_passed'])

    def main_mocked(self, identical=False, fail_correctness=False):
        config_path = self.out / "input.yaml"
        config_path.write_text(yaml.safe_dump(dict(schema_version=1,
            defaults=dict(resolution="320x180", fps=60, codec="av1", dynamic_range="sdr", frames=3),
            run=dict(seconds=1, repetitions=3, warmup_frames=0),
            cases=[dict(name="first"), dict(name="second")])))
        results = self.out / "results"
        observed, analyzed = [], []

        def build_info(build, setting, revision, out):
            return dict(binary="/synthetic/" + setting, binary_sha256="same" if identical else setting,
                        environment=dict(architecture="arm64", compiler="test compiler", sdk="test SDK",
                                         deployment_target="11.0", cmake_cache={}))

        def invoke(plan, out, case, setting, phase, repetition):
            record = dict(case=case["name"], setting=setting, phase=phase, repetition=repetition)
            observed.append(record.copy())
            plan["runs"].append(record)
            return record

        def inspect(record, case, out, thresholds):
            fail = fail_correctness and record["phase"] == "correctness" and record["setting"] == "baseline"
            return dict(passed=not fail, errors=["synthetic correctness failure"] if fail else [])

        def analyze(plan, out):
            analyzed.append(copy.deepcopy(plan))
            return dict(status="FAIL" if plan["state"] == "ERROR" else "PASS")

        with mock.patch.object(RUNNER, "build_info", side_effect=build_info), \
             mock.patch.object(RUNNER, "prepare_fixture", return_value=self.case["fixture_info"]), \
             mock.patch.object(RUNNER, "invoke", side_effect=invoke), \
             mock.patch.object(RUNNER, "inspect_run", side_effect=inspect), \
             mock.patch.object(RUNNER, "analyze", side_effect=analyze), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = RUNNER.main(["--config", str(config_path), "--candidate-build", "/candidate",
                                "--baseline-build", "/baseline", "--results-dir", str(results)])
        return code, observed, analyzed[-1]

    def test_all_correctness_gates_precede_alternating_case_and_pair_order(self):
        code, observed, plan = self.main_mocked()
        self.assertEqual(code, 0)
        self.assertEqual(plan["state"], "FINISHED")
        self.assertEqual([r["phase"] for r in observed[:4]], ["correctness"] * 4)
        self.assertTrue(all(r["phase"] == "timed" for r in observed[4:]))
        self.assertEqual([r["setting"] for r in observed[4:10]],
                         ["baseline", "candidate", "candidate", "baseline", "baseline", "candidate"])
        self.assertEqual([r["setting"] for r in observed[10:16]],
                         ["candidate", "baseline", "baseline", "candidate", "candidate", "baseline"])
        self.assertEqual([r["repetition"] for r in observed[4:10]], [1, 1, 2, 2, 3, 3])

    def test_failed_correctness_gate_skips_timing_for_affected_cases(self):
        _, observed, plan = self.main_mocked(fail_correctness=True)
        self.assertEqual(len(observed), 4)
        self.assertTrue(all(r["phase"] == "correctness" for r in observed))
        self.assertTrue(all("correctness gate failed" in case["error"] for case in plan["cases"]))

    def test_identical_baseline_candidate_binaries_do_not_validate_an_upgrade(self):
        code, observed, plan = self.main_mocked(identical=True)
        self.assertEqual(code, 1)
        self.assertEqual(observed, [])
        self.assertEqual(plan["state"], "ERROR")

    def test_attempt_is_journaled_before_execution_and_timeout_is_retained(self):
        binary = self.out / "mav-replay"
        binary.write_bytes(b"synthetic binary; never executed")
        plan = dict(config=dict(run=dict(seconds=1, warmup_frames=0, timeout_seconds=180)),
                    builds=dict(candidate=dict(binary=str(binary), binary_sha256=RUNNER.sha(binary))), runs=[])

        def execute(command, **kwargs):
            saved = RUNNER.read_json(self.out / "plan.json")
            self.assertEqual(len(saved["runs"]), 1)
            self.assertEqual(saved["runs"][0]["state"], "RUNNING")
            self.assertEqual(saved["runs"][0]["command"], command)
            self.assertEqual(kwargs["timeout"], 180)
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])

        with mock.patch.object(RUNNER, "verify_fixture", return_value=(self.case["fixture_info"], None)), \
             mock.patch.object(RUNNER.subprocess, "run", side_effect=execute), \
             contextlib.redirect_stdout(io.StringIO()):
            record = RUNNER.invoke(plan, self.out, self.case, "candidate", "timed", 1)
        self.assertEqual(record["state"], "ERROR")
        self.assertIsNone(record["exit_code"])
        self.assertIsNone(record["result_file_sha256"])
        self.assertIn("timed out", record["error"])
        self.assertEqual(RUNNER.read_json(self.out / "plan.json")["runs"][0], record)


if __name__ == "__main__":
    unittest.main()
