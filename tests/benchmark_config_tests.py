#!/usr/bin/env python3
"""Portable tests of benchmark YAML semantics, limits and rejection behavior."""

import copy
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import benchmark_config
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = {
    "schema_version": 1,
    "defaults": {
        "resolution": "1920x1080", "fps": 60, "codec": "av1", "dynamic_range": "sdr",
    },
    "cases": [{}],
}


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mav-yaml-test-")
        self.directory = pathlib.Path(self.temporary.name)
        self.path = self.directory / "config.yaml"

    def tearDown(self):
        self.temporary.cleanup()

    def load(self, data=None, source=None):
        self.path.write_text(source if source is not None else yaml.safe_dump(data), encoding="utf-8")
        return benchmark_config.load_config(self.path)

    def reject(self, data=None, source=None, message=None):
        with self.assertRaisesRegex(benchmark_config.ConfigError, message or ".+"):
            self.load(data, source)

    def test_normalized_api_and_defaults(self):
        result = self.load(BASE)
        self.assertEqual(set(result), {"schema_version", "run", "thresholds", "cases"})
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["run"], benchmark_config.RUN_DEFAULTS)
        self.assertEqual(result["thresholds"], benchmark_config.THRESHOLD_DEFAULTS)
        self.assertEqual(result["cases"], [{
            "name": "1920x1080p60-av1-sdr-legacy", "width": 1920, "height": 1080,
            "fps": 60, "codec": "av1", "dynamic_range": "sdr", "bitrate_kbps": None,
            "gop": 60, "frames": 120, "fixture": None,
            "decoder": benchmark_config.DECODER_DEFAULTS,
        }])

    def test_full_example_covers_requested_matrix(self):
        result = benchmark_config.load_config(ROOT / "benchmarks/full-matrix.yaml")
        self.assertEqual(len(result["cases"]), 24)
        self.assertEqual({(c["width"], c["height"], c["fps"]) for c in result["cases"]}, {
            (1920, 1080, 60), (1920, 1080, 120), (3440, 1440, 120),
            (3440, 1440, 240), (3840, 2160, 60), (3840, 2160, 120),
        })
        for width, height, fps in {(c["width"], c["height"], c["fps"]) for c in result["cases"]}:
            cases = [c for c in result["cases"] if (c["width"], c["height"], c["fps"]) == (width, height, fps)]
            self.assertEqual({(c["codec"], c["dynamic_range"]) for c in cases}, {
                ("av1", "sdr"), ("av1", "hdr10"), ("hevc", "sdr"), ("hevc", "hdr10"),
            })
            self.assertTrue(all(c["frames"] == max(120, fps) and c["bitrate_kbps"] is None for c in cases))

    def test_small_examples_preserve_target_bitrate_and_queue_policy(self):
        smoke = benchmark_config.load_config(ROOT / "benchmarks/smoke.yaml")
        self.assertEqual(len(smoke["cases"]), 2)
        self.assertEqual({c["codec"] for c in smoke["cases"]}, {"av1", "hevc"})
        self.assertTrue(all(c["bitrate_kbps"] == 1000 for c in smoke["cases"]))
        followup = benchmark_config.load_config(ROOT / "benchmarks/full-matrix-q32.yaml")
        self.assertEqual(len(followup["cases"]), 2)
        self.assertTrue(all(c["decoder"]["queue_depth"] == 32 for c in followup["cases"]))
        self.assertTrue(all(c["codec"] == "av1" and c["fps"] == 240 for c in followup["cases"]))

    def test_cartesian_axes_and_decoder_merge_do_not_share_mutable_state(self):
        data = copy.deepcopy(BASE)
        data["defaults"].update({"fps": [60, 120], "codec": ["hevc", "av1"],
                                "dynamic_range": ["sdr", "hdr10"], "bitrate_kbps": [None, 10000],
                                "decoder": {"inflight": 3, "queue_depth": 16}})
        data["cases"] = [{"name": "desk", "resolution": "3440x1440", "decoder": {"queue_depth": 32}}]
        result = self.load(data)
        self.assertEqual(len(result["cases"]), 16)
        self.assertEqual(len({c["name"] for c in result["cases"]}), 16)
        self.assertEqual(result["cases"][0]["name"], "desk-3440x1440p60-hevc-sdr-legacy")
        self.assertTrue(all(c["decoder"]["inflight"] == 3 and c["decoder"]["queue_depth"] == 32 for c in result["cases"]))
        result["cases"][0]["decoder"]["inflight"] = 1
        self.assertEqual(result["cases"][1]["decoder"]["inflight"], 3)
        self.assertEqual(data["defaults"]["decoder"]["queue_depth"], 16)

    def test_relative_fixture_resolves_from_yaml_directory_without_executing_text(self):
        data = copy.deepcopy(BASE)
        data["cases"] = [{"fixture": "fixtures/$(touch pwned);captured.json"}]
        case = self.load(data)["cases"][0]
        self.assertEqual(case["fixture"], str((self.directory / "fixtures/$(touch pwned);captured.json").resolve()))
        self.assertFalse((self.directory / "pwned").exists())

    def test_explicit_dimensions_override_resolution_defaults(self):
        data = copy.deepcopy(BASE)
        data["cases"] = [{"width": 3840, "height": 2160}]
        case = self.load(data)["cases"][0]
        self.assertEqual((case["width"], case["height"]), (3840, 2160))

    def test_unknown_client_and_command_options_are_rejected(self):
        variants = [
            ("", "command", "touch pwned"), ("defaults", "chroma", "444"),
            ("defaults", "vsync", True), ("defaults", "audio", "stereo"),
            ("defaults", "bit_depth", 10), ("defaults", "hdr", True),
            ("run", "shell", True), ("thresholds", "ignore_failures", True),
        ]
        for section, key, value in variants:
            with self.subTest(section=section, key=key):
                data = copy.deepcopy(BASE)
                target = data.setdefault(section, {}) if section else data
                target[key] = value
                self.reject(data, message="unsupported key")
        data = copy.deepcopy(BASE)
        data["cases"] = [{"decoder": {"realtime": 0}}]
        self.reject(data, message="unsupported key")

    def test_missing_required_fields_and_bad_resolution_are_errors(self):
        for key in ("resolution", "fps", "codec", "dynamic_range"):
            data = copy.deepcopy(BASE)
            del data["defaults"][key]
            self.reject(data, message="missing required")
        for resolution in ("4k", "1920 X 1080", "1920x", [1920, 1080], True, "1920x1081"):
            data = copy.deepcopy(BASE)
            data["defaults"]["resolution"] = resolution
            self.reject(data)
        for case in ({"resolution": "1920x1080", "width": 1920}, {"width": 3840}):
            data = copy.deepcopy(BASE)
            data["cases"] = [case]
            self.reject(data)

    def test_invalid_numeric_stream_and_decoder_values(self):
        fields = {
            "fps": [True, 60.0, "60", 0, 1001, float("nan")],
            "bitrate_kbps": [True, 0, -1, 1000001, 1000.1, "10000"],
            "frames": [True, 1, 100001], "gop": [True, 0, 100001],
            "codec": ["h264", "AV1", True], "dynamic_range": ["dolby_vision", "hdr", True],
        }
        for field, values in fields.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(BASE)
                    data["cases"] = [{field: value}]
                    self.reject(data)
        for field, values in {
            "inflight": [True, 0, 4], "queue_depth": [True, 0, 4097],
            "power": [True, 1, -2, 0.0], "consumer_delay_ms": [-1, 10001],
            "jitter_us": [-1, 1000001], "seed": [True, -1, 4294967296],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(BASE)
                    data["cases"] = [{"decoder": {field: value}}]
                    self.reject(data)

    def test_run_limits_and_warmup_must_leave_samples(self):
        for field, values in {
            "seconds": [True, 0, 601, 1.5], "repetitions": [True, 0, 21],
            "warmup_frames": [-1, True, 600], "timeout_seconds": [0, 10, 3601, True],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(BASE)
                    data["run"] = {field: value}
                    self.reject(data)
        data = copy.deepcopy(BASE)
        data["run"] = {"seconds": 600}
        self.assertEqual(self.load(data)["run"]["timeout_seconds"], 660)
        data["run"] = {"seconds": 1, "warmup_frames": 119}
        self.assertEqual(self.load(data)["run"]["warmup_frames"], 119)

    def test_thresholds_are_finite_numeric_and_bounded(self):
        for field, values in {
            "decoded_fps_ratio": [True, 0, 1.01, float("nan"), "0.99"],
            "latency_relative_pct": [True, -1, 1001, 10 ** 1000, float("inf")],
            "latency_absolute_ms": [True, -1, 1001, float("-inf")],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    data = copy.deepcopy(BASE)
                    data["thresholds"] = {field: value}
                    self.reject(data)
        data = copy.deepcopy(BASE)
        data["thresholds"] = {"latency_relative_pct": 0, "latency_absolute_ms": 0}
        self.assertEqual(self.load(data)["thresholds"]["latency_relative_pct"], 0.0)

    def test_native_loop_limit_and_rounded_duration_are_validated(self):
        data = copy.deepcopy(BASE)
        data["defaults"].update(fps=1000, frames=2)
        data["run"] = dict(seconds=600, warmup_frames=0)
        self.reject(data, message="native limits")
        data["defaults"].update(fps=1, frames=100000)
        data["run"] = dict(seconds=1, warmup_frames=0)
        self.reject(data, message="rounded paced duration")
        data["defaults"].update(fps=1, frames=500)
        data["run"] = dict(seconds=600, warmup_frames=0)
        self.assertEqual(self.load(data)["run"]["timeout_seconds"], 1060)
        data["run"]["timeout_seconds"] = 1000
        self.reject(data, message="rounded paced duration")
        data["run"]["timeout_seconds"] = 1001
        self.assertEqual(self.load(data)["run"]["timeout_seconds"], 1001)

    def test_duplicate_keys_aliases_tags_and_yaml_execution_are_rejected(self):
        for source in (
            "schema_version: 1\nschema_version: 1\ncases: []\n",
            "schema_version: 1\ndefaults: {fps: 60, fps: 120}\ncases: []\n",
            "schema_version: 1\ndefaults: &defaults {fps: 60}\ncases: [*defaults]\n",
            "schema_version: 1\ncases: &cycle [*cycle]\n",
            "schema_version: 1\ncases: [{<<: {fps: 60}}]\n",
            "!!python/object/apply:os.system ['touch pwned']\n",
            "schema_version: !!int 1\ncases: []\n",
            "1: invalid-key\n",
            "? [complex, key]\n: invalid\n",
        ):
            with self.subTest(source=source):
                self.reject(source=source)
        self.assertFalse((self.directory / "pwned").exists())

    def test_empty_malformed_multidocument_and_oversized_files(self):
        for source in ("", "[]", "null", "schema_version: [", "---\n{}\n---\n{}\n", "x" * (benchmark_config.MAX_CONFIG_BYTES + 1)):
            self.reject(source=source)
        self.path.write_bytes(b"\xff")
        with self.assertRaises(benchmark_config.ConfigError):
            benchmark_config.load_config(self.path)
        self.path.unlink()
        with self.assertRaisesRegex(benchmark_config.ConfigError, "cannot read"):
            benchmark_config.load_config(self.path)

    def test_version_list_case_and_expansion_limits(self):
        for version in (None, True, 1.0, "1", 2):
            data = copy.deepcopy(BASE)
            data["schema_version"] = version
            self.reject(data, message="schema_version")
        for cases in (None, {}, [], [False], [{}] * 257):
            data = copy.deepcopy(BASE)
            data["cases"] = cases
            self.reject(data)
        for field in benchmark_config.EXPANDABLE:
            data = copy.deepcopy(BASE)
            data["defaults"][field] = []
            self.reject(data)
        data = copy.deepcopy(BASE)
        data["defaults"].update({"fps": list(range(1, 130)), "codec": ["av1", "hevc"]})
        self.reject(data, message="256 case limit")

    def test_case_names_and_duplicates_cannot_overwrite_results(self):
        for name in (None, "", "../escape", "contains spaces", "-start", "a" * 65, True):
            data = copy.deepcopy(BASE)
            data["cases"] = [{"name": name}]
            self.reject(data)
        for cases in ([{}, {}], [{"fps": [60, 60]}], [{"decoder": {"inflight": 1}}, {"decoder": {"inflight": 2}}]):
            data = copy.deepcopy(BASE)
            data["cases"] = cases
            self.reject(data, message="duplicate expanded case name")
        data = copy.deepcopy(BASE)
        data["cases"] = [{"name": "first"}, {"name": "second"}]
        self.assertEqual(len(self.load(data)["cases"]), 2)

    def test_fixture_rejects_url_empty_nul_and_nonpath_values(self):
        for fixture in ("", "  ", "https://example.com/manifest.json", "a\x00b", 123, True, ["path"]):
            data = copy.deepcopy(BASE)
            data["cases"] = [{"fixture": fixture}]
            self.reject(data)


if __name__ == "__main__":
    unittest.main()
