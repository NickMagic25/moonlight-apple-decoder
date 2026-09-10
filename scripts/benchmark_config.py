#!/usr/bin/env python3
"""Strict, portable YAML input for decoder benchmarks.

load_config() returns only normalized JSON-compatible values. YAML supplies data,
never commands. Paths in ``fixture`` are relative to the configuration file.
"""

import itertools
import math
import pathlib
import re
from decimal import Decimal

try:
    import yaml
except ImportError as error:
    raise ImportError(
        "Benchmark YAML support requires: python3 -m pip install -r "
        "scripts/requirements-benchmarks.txt"
    ) from error


MAX_CONFIG_BYTES = 1024 * 1024
MAX_CASES = 256
EXPANDABLE = ("fps", "codec", "dynamic_range", "bitrate_mbps")
STREAM_KEYS = {
    "resolution", "width", "height", "fps", "codec", "dynamic_range",
    "bitrate_mbps", "gop", "frames", "fixture", "decoder",
}
DECODER_DEFAULTS = {
    "inflight": 2, "queue_depth": 16, "power": -1,
    "consumer_delay_ms": 0, "jitter_us": 0, "seed": 7, "startup_grace_ms": 0,
}
RUN_DEFAULTS = {
    "seconds": 10, "repetitions": 3, "warmup_frames": 120,
    "timeout_seconds": 180,
}
THRESHOLD_DEFAULTS = {
    "decoded_fps_ratio": 0.99, "latency_relative_pct": 5.0,
    "latency_absolute_ms": 0.1, "bitrate_tolerance_pct": 20.0,
    "first_output_max_ms": None,
}


class ConfigError(ValueError):
    """A configuration is unsupported, ambiguous or invalid."""


class _UniqueLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            raise ConfigError("expected a YAML mapping")
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str):
                raise ConfigError("all YAML keys must be strings")
            if key in result:
                raise ConfigError("duplicate YAML key: {!r}".format(key))
            if key == "<<":
                raise ConfigError("YAML merge keys are unsupported; use defaults")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _mapping(value, location, allowed):
    if not isinstance(value, dict):
        raise ConfigError("{} must be a mapping".format(location))
    unknown = sorted(set(value) - set(allowed))
    if unknown:
        raise ConfigError("{} has unsupported key(s): {}".format(
            location, ", ".join(unknown)))
    return value


def _integer(value, location, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ConfigError("{} must be an integer from {} to {}".format(
            location, minimum, maximum))
    return value


def _number(value, location, minimum, maximum):
    if (type(value) not in (int, float) or not minimum <= value <= maximum
            or not math.isfinite(value)):
        raise ConfigError("{} must be a finite number from {} to {}".format(
            location, minimum, maximum))
    return float(value)


def _choice(value, location, options):
    if not isinstance(value, str) or value not in options:
        raise ConfigError("{} must be one of: {}".format(
            location, ", ".join(options)))
    return value


def _bitrate_mbps(value, location):
    """Keep the public unit in Mbps without rounding encoder kbps targets."""
    _number(value, location, 0.001, 1000)
    kbps = Decimal(str(value)) * 1000
    if kbps != kbps.to_integral_value():
        raise ConfigError(location + " must have at most 0.001 Mbps precision (1 kbps)")
    return int(kbps) / 1000.0


def _stream_mapping(value, location, allow_name=False):
    """Normalize resolution before merging, so case dimensions override defaults."""
    if isinstance(value, dict) and "bitrate_kbps" in value:
        raise ConfigError(location + ".bitrate_kbps is unsupported; use bitrate_mbps in decimal "
                          "megabits per second (divide the old kbps value by 1000)")
    result = dict(_mapping(value, location, STREAM_KEYS | ({"name"} if allow_name else set())))
    if "resolution" in result:
        if "width" in result or "height" in result:
            raise ConfigError("{} must use resolution or width/height, not both".format(location))
        resolution = result.pop("resolution")
        match = re.fullmatch(r"([0-9]{2,4})x([0-9]{2,4})", resolution) if isinstance(resolution, str) else None
        if not match:
            raise ConfigError("{}.resolution must be a WIDTHxHEIGHT string, for example 1920x1080".format(location))
        result["width"], result["height"] = map(int, match.groups())
    elif ("width" in result) != ("height" in result):
        raise ConfigError("{} must specify width and height together".format(location))
    if "decoder" in result:
        _mapping(result["decoder"], location + ".decoder", DECODER_DEFAULTS)
    return result


def _decoder(value, location):
    normalized = dict(DECODER_DEFAULTS)
    normalized.update(_mapping(value, location, DECODER_DEFAULTS))
    for key, bounds in {
        "inflight": (1, 3), "queue_depth": (1, 4096),
        "consumer_delay_ms": (0, 10000), "jitter_us": (0, 1000000),
        "startup_grace_ms": (0, 10000),
        "seed": (0, 4294967295),
    }.items():
        normalized[key] = _integer(normalized[key], location + "." + key, *bounds)
    if type(normalized["power"]) is not int or normalized["power"] not in (-1, 0):
        raise ConfigError(location + ".power must be -1 (system default) or 0 (prefer performance)")
    return normalized


def _one_case(value, location, directory):
    required = {"width", "height", "fps", "codec", "dynamic_range"}
    missing = sorted(required - set(value))
    if missing:
        raise ConfigError("{} is missing required setting(s): {}".format(location, ", ".join(missing)))
    result = {}
    for key in ("width", "height"):
        result[key] = _integer(value[key], location + "." + key, 64, 8192)
        if result[key] % 2:
            raise ConfigError("{}.{} must be even for 4:2:0 video".format(location, key))
    result["fps"] = _integer(value["fps"], location + ".fps", 1, 1000)
    result["codec"] = _choice(value["codec"], location + ".codec", ("av1", "hevc"))
    result["dynamic_range"] = _choice(value["dynamic_range"], location + ".dynamic_range", ("sdr", "hdr10"))
    bitrate = value.get("bitrate_mbps")
    result["bitrate_mbps"] = None if bitrate is None else _bitrate_mbps(
        bitrate, location + ".bitrate_mbps")
    result["gop"] = _integer(value.get("gop", 60), location + ".gop", 1, 100000)
    result["frames"] = _integer(value.get("frames", max(120, result["fps"])), location + ".frames", 2, 100000)
    fixture = value.get("fixture")
    if fixture is not None:
        if not isinstance(fixture, str) or not fixture.strip() or "\x00" in fixture:
            raise ConfigError(location + ".fixture must be a nonempty local path or null")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", fixture):
            raise ConfigError(location + ".fixture must be a local path, not a URL")
        fixture = str((directory / fixture).resolve())
    result["fixture"] = fixture
    result["decoder"] = _decoder(value.get("decoder", {}), location + ".decoder")
    prefix = value.get("name")
    if "name" in value and (not isinstance(prefix, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", prefix)):
        raise ConfigError(location + ".name must contain 1 to 64 letters, digits, underscores or hyphens and start with a letter or digit")
    generated = "{width}x{height}p{fps}-{codec}-{dynamic_range}-{bitrate}".format(
        bitrate="legacy" if bitrate is None else "{:g}mbps".format(result["bitrate_mbps"]), **result)
    result["name"] = "{}-{}".format(prefix, generated) if prefix else generated
    return result


def load_config(path):
    """Read schema version 1 and expand stream lists to independent case dicts.

    Explicit fixture paths are made absolute but read/validated by the runner.
    Unknown client features are errors; the headless harness cannot model the
    renderer, network transport, audio, chroma 4:4:4 or Dolby Vision.
    """
    path = pathlib.Path(path).resolve()
    try:
        with path.open("rb") as handle:
            content = handle.read(MAX_CONFIG_BYTES + 1)
        if len(content) > MAX_CONFIG_BYTES:
            raise ConfigError("configuration exceeds the 1 MiB limit")
        source = content.decode("utf-8")
        # Anchors/aliases and custom tags are unnecessary for this small schema.
        # Reject them before construction, including cyclic or expanding aliases.
        for event in yaml.parse(source, Loader=_UniqueLoader):
            if isinstance(event, yaml.AliasEvent) or getattr(event, "anchor", None):
                raise ConfigError("YAML anchors and aliases are unsupported; use defaults")
            if getattr(event, "tag", None):
                raise ConfigError("explicit YAML tags are unsupported")
        document = yaml.load(source, Loader=_UniqueLoader)
    except (OSError, UnicodeError, yaml.YAMLError, RecursionError) as error:
        raise ConfigError("cannot read benchmark configuration {}: {}".format(path, error)) from error
    document = _mapping(document, "configuration", {"schema_version", "defaults", "run", "thresholds", "cases"})
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise ConfigError("schema_version must be the integer 1")
    defaults = _stream_mapping(document.get("defaults", {}), "defaults")
    run = dict(RUN_DEFAULTS)
    run_input = _mapping(document.get("run", {}), "run", RUN_DEFAULTS)
    run.update(run_input)
    for key, bounds in {"seconds": (1, 600), "repetitions": (1, 20),
                        "warmup_frames": (0, 1000000), "timeout_seconds": (1, 3600)}.items():
        run[key] = _integer(run[key], "run." + key, *bounds)
    if "timeout_seconds" not in run_input:
        run["timeout_seconds"] = max(run["timeout_seconds"], run["seconds"] + 60)
    if run["timeout_seconds"] <= run["seconds"]:
        raise ConfigError("run.timeout_seconds must exceed run.seconds to allow decoder drain")
    thresholds = dict(THRESHOLD_DEFAULTS)
    thresholds.update(_mapping(document.get("thresholds", {}), "thresholds", THRESHOLD_DEFAULTS))
    for key, bounds in {"decoded_fps_ratio": (0.01, 1.0), "latency_relative_pct": (0.0, 1000.0),
                        "latency_absolute_ms": (0.0, 1000.0), "bitrate_tolerance_pct": (0.0, 100.0)}.items():
        thresholds[key] = _number(thresholds[key], "thresholds." + key, *bounds)
    if thresholds["first_output_max_ms"] is not None:
        thresholds["first_output_max_ms"] = _number(
            thresholds["first_output_max_ms"], "thresholds.first_output_max_ms", 0, 60000)
        if thresholds["first_output_max_ms"] == 0:
            raise ConfigError("thresholds.first_output_max_ms must be positive or null to disable")
    case_inputs = document.get("cases")
    if not isinstance(case_inputs, list) or not 1 <= len(case_inputs) <= MAX_CASES:
        raise ConfigError("cases must be a nonempty list with at most {} entries".format(MAX_CASES))
    cases, names = [], set()
    longest_duration = 0.0
    for index, case_input in enumerate(case_inputs):
        location = "cases[{}]".format(index)
        case_input = _stream_mapping(case_input, location, allow_name=True)
        merged = dict(defaults)
        merged.update(case_input)
        merged["decoder"] = dict(defaults.get("decoder", {}))
        merged["decoder"].update(case_input.get("decoder", {}))
        axes = []
        for key in EXPANDABLE:
            if key not in merged:
                if key == "bitrate_mbps":
                    merged[key] = None
                else:
                    raise ConfigError("{} is missing required setting: {}".format(location, key))
            values = merged[key] if isinstance(merged[key], list) else [merged[key]]
            if not values or len(values) > MAX_CASES:
                raise ConfigError("{}.{} must have 1 to {} values".format(location, key, MAX_CASES))
            axes.append(values)
        if len(cases) + math.prod(map(len, axes)) > MAX_CASES:
            raise ConfigError("configuration expands beyond the {} case limit".format(MAX_CASES))
        for combination in itertools.product(*axes):
            expanded = dict(merged)
            expanded.update(zip(EXPANDABLE, combination))
            normalized = _one_case(expanded, location, path.parent)
            loops = math.ceil(run["seconds"] * normalized["fps"] / normalized["frames"])
            offered = loops * normalized["frames"]
            if loops > 10000 or offered > 1000000:
                raise ConfigError("{} exceeds native limits of 10000 loops or 1000000 offered frames; "
                                  "reduce run.seconds or increase fixture frames".format(location))
            longest_duration = max(longest_duration, offered / normalized["fps"])
            if run["warmup_frames"] >= offered or offered < 2:
                raise ConfigError("{}.warmup_frames excludes all steady samples ({} offered frames)".format(
                    "run", offered))
            if normalized["name"] in names:
                raise ConfigError("duplicate expanded case name: {} (use distinct name prefixes)".format(normalized["name"]))
            names.add(normalized["name"])
            cases.append(normalized)
    if "timeout_seconds" not in run_input:
        run["timeout_seconds"] = max(run["timeout_seconds"], math.ceil(longest_duration) + 60)
    if run["timeout_seconds"] > 3600 or run["timeout_seconds"] <= longest_duration:
        raise ConfigError("run.timeout_seconds must exceed the longest rounded paced duration "
                          "({:.3f} seconds) and remain at most 3600; reduce fixture frames or increase "
                          "timeout_seconds".format(longest_duration))
    return {"schema_version": 1, "run": run, "thresholds": thresholds, "cases": cases}
