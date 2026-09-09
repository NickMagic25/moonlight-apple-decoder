#!/usr/bin/env python3
"""Run reproducible, serial hardware comparisons from a strict YAML matrix.

Builds are explicit inputs. Fixture generation and correctness gates precede
timing. Every attempted invocation is journaled before execution; raw evidence
is never rewritten by analysis. A missing run or failed baseline cannot pass.
"""
import argparse
import copy
import csv
import datetime
from decimal import Decimal
import hashlib
import json
import math
import os
import pathlib
import shutil
import signal
import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET

from benchmark_config import load_config
from benchmark_analysis import caller_timings, distribution
from benchmark_reference import (SOURCE_PATTERN, REFERENCE_PATTERN, requires_reference,
                                 prepare_reference, validate_reference, cleanup_reference)
from environment import capture

ROOT = pathlib.Path(__file__).resolve().parents[1]
METRICS = {f'{boundary}_{quantile}_ms': (field, quantile)
           for boundary, field in [('vt', 'vt_submit_to_callback_ns'),
                                   ('public', 'public_complete_au_to_output_ns')]
           for quantile in ('median', 'p95', 'p99')}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def read_json(path):
    def invalid(value):
        raise ValueError('non-finite JSON number: ' + value)
    return json.loads(path.read_text(), parse_constant=invalid)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def cmake_cache(build):
    result = {}
    for line in (build / 'CMakeCache.txt').read_text().splitlines():
        if '=' in line and not line.startswith(('#', '//')):
            key, value = line.split('=', 1)
            result[key.split(':')[0]] = value
    return result


def build_info(build, label, revision, out):
    build = build.resolve()
    binary = build / 'mav-replay'
    if not binary.is_file() or not os.access(binary, os.X_OK):
        raise ValueError(f'{label}: executable mav-replay missing in {build}')
    cache = cmake_cache(build)
    if cache.get('CMAKE_BUILD_TYPE') != 'Release':
        raise ValueError(f'{label}: a Release build is required')
    for key in ('MAV_SANITIZE', 'MAV_VT_EXPERIMENTS'):
        if cache.get(key) not in ('OFF', 'FALSE', '0', None):
            raise ValueError(f'{label}: {key} must be OFF for production comparisons')
    source = pathlib.Path(cache['CMAKE_HOME_DIRECTORY']).resolve()
    environment = capture(source, build, out / f'{label}-environment.json')
    environment['declared_revision'] = revision
    environment['build_directory'] = str(build)
    environment['source_directory'] = str(source)
    environment['cmake_cache'] = {key: value for key, value in cache.items()
                                  if key.startswith(('CMAKE_CXX_', 'CMAKE_OBJCXX_', 'CMAKE_OSX_', 'MAV_'))}
    commands = build / 'compile_commands.json'
    environment['compile_commands_sha256'] = sha(commands) if commands.is_file() else None
    if commands.is_file():
        shutil.copyfile(commands, out / f'{label}-compile-commands.json')
    shutil.copyfile(build / 'CMakeCache.txt', out / f'{label}-CMakeCache.txt')
    # An archive can have no .git. Declared revisions remain labels, alongside
    # actual source and executable hashes, rather than overriding observed data.
    write_json(out / f'{label}-environment.json', environment)
    return dict(build=str(build), binary=str(binary), binary_sha256=sha(binary),
                environment=environment)


def requested_mbps(fields, key='bitrate_mbps', legacy_key='bitrate_kbps'):
    """Read explicit units without treating booleans or conflicting labels as rates."""
    requested = fields.get(key)
    if requested is not None:
        if (type(requested) not in (int, float) or not 0.001 <= requested <= 1000
                or not math.isfinite(requested)
                or Decimal(str(requested)) * 1000 != (Decimal(str(requested)) * 1000).to_integral_value()):
            raise ValueError('invalid requested bitrate in Mbps')
    if legacy_key in fields:
        legacy = fields[legacy_key]
        if legacy is not None and (type(legacy) is not int or not 1 <= legacy <= 1000000):
            raise ValueError('invalid legacy requested bitrate in kbps')
        converted = None if legacy is None else legacy / 1000
        if key in fields and requested != converted:
            raise ValueError('conflicting requested bitrate units')
        requested = converted
    return requested


def normalize_plan_bitrates(plan):
    """Allow analysis of earlier kbps archives without rewriting source evidence."""
    plan = copy.deepcopy(plan)
    for case in plan['cases'] + plan['config'].get('cases', []):
        case['bitrate_mbps'] = requested_mbps(case)
        case.pop('bitrate_kbps', None)
        info = case.get('fixture_info', {})
        if 'requested_bitrate_kbps' in info:
            info['requested_bitrate_mbps'] = requested_mbps(info, 'requested_bitrate_mbps', 'requested_bitrate_kbps')
            del info['requested_bitrate_kbps']
        if 'measured_bitrate_kbps' in info:
            info['measured_bitrate_mbps'] = info.pop('measured_bitrate_kbps') / 1000
    return plan


def bitrate_covered(requested, measured, tolerance):
    if requested is None or measured is None:
        return None
    # Compare the recorded decimal values so an inclusive +10% boundary such
    # as 55 Mbps versus 50 Mbps is not rejected by binary float division.
    return (abs(Decimal(str(measured)) - Decimal(str(requested))) * 100
            <= Decimal(str(requested)) * Decimal(str(tolerance)))


def verify_fixture(path, case):
    """Check requested settings and byte identity before the native parser gate."""
    manifest = read_json(path)
    if not isinstance(manifest, dict):
        raise ValueError('fixture manifest must be an object')
    generator = manifest.get('generator')
    if (not isinstance(generator, dict)
            or generator.get('pattern') not in (SOURCE_PATTERN, REFERENCE_PATTERN)):
        raise ValueError('fixture must use a supported correctness validation pattern')
    expected = dict(width=case['width'], height=case['height'], codec=case['codec'],
                    variant='sdr8' if case['dynamic_range'] == 'sdr' else 'hdr10',
                    bit_depth=8 if case['dynamic_range'] == 'sdr' else 10, chroma='420')
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f'fixture {key} does not match requested {value}')
    rate = manifest['frame_rate']
    if rate['num'] != case['fps'] * rate['den'] or rate['den'] <= 0:
        raise ValueError('fixture frame rate differs from requested frame rate')
    relative = pathlib.Path(manifest['payload_file'])
    payload = (path.parent / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or path.parent.resolve() not in payload.parents:
        raise ValueError('fixture payload must stay inside its manifest directory')
    if sha(payload) != manifest['payload_sha256']:
        raise ValueError('fixture payload hash mismatch')
    units = manifest['access_units']
    if len(units) != case['frames']:
        raise ValueError('fixture frame count differs from requested frames')
    # The headless pattern correctness sink requires sequential visible IDs.
    for index, unit in enumerate(units):
        if (unit.get('frame_id') != index or unit.get('expected_display_count') != 1
                or type(unit.get('expected_visible_frame_id')) is not int
                or unit['expected_visible_frame_id'] != index
                or unit.get('pts') != index or unit.get('duration') != 1
                or unit.get('discontinuity') or bool(unit.get('random_access')) != (index % case['gop'] == 0)):
            raise ValueError('fixture must use sequential one-output frames and the requested GOP')
    if manifest['timebase'] != dict(num=1, den=case['fps']):
        raise ValueError('fixture timebase differs from requested frame rate')
    # Previously generated fixtures used kbps. Interpret that explicit unit,
    # never relabel its numeric value as Mbps or modify the archived manifest.
    requested = requested_mbps(generator, 'requested_bitrate_mbps', 'requested_bitrate_kbps')
    if requested != case['bitrate_mbps']:
        raise ValueError('fixture requested bitrate differs from YAML; regenerate with matching settings')
    return dict(manifest_sha256=sha(path), payload_sha256=sha(payload),
                payload_file=manifest['payload_file'], frames=len(units),
                requested_bitrate_mbps=requested,
                measured_bitrate_mbps=payload.stat().st_size * 8 * case['fps'] / len(units) / 1000000,
                generator=generator), payload


def run_encoder(command, log, timeout):
    """Bound fixture execution and clean up children that inherit its group."""
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                               start_new_session=True)
    try:
        return subprocess.CompletedProcess(command, process.wait(timeout=timeout))
    except BaseException:
        # Kill inheriting children as well as mav-fixture. A launcher may create
        # separate child groups, so preparation failure must also prevent timing.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # The entire group already exited.
        process.wait()
        raise


def prepare_fixture(case, fixture_build, aomenc, out, timeout):
    variant = 'sdr8' if case['dynamic_range'] == 'sdr' else 'hdr10'
    command = None
    if case['fixture']:
        path = pathlib.Path(case['fixture'])
    else:
        legacy = ROOT / 'fixtures/generated' / (
            f"{case['codec']}-{variant}-{case['width']}x{case['height']}p{case['fps']}-{case['frames']}") / 'manifest.json'
        if case['bitrate_mbps'] is None and case['gop'] == 60 and legacy.is_file():
            path = legacy
        else:
            binary = fixture_build / 'mav-fixture'
            settings = {key: case[key] for key in ('width', 'height', 'fps', 'codec', 'dynamic_range', 'bitrate_mbps', 'gop', 'frames')}
            settings['generator_sha256'] = sha(binary)
            if case['codec'] == 'av1':
                settings['aomenc_sha256'] = sha(aomenc)
            identity = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
            directory = ROOT / 'fixtures/generated/matrix' / identity
            path = directory / 'manifest.json'
            if not path.is_file():
                directory.mkdir(parents=True, exist_ok=True)
                command = [str(binary), '--codec', case['codec'], '--variant', variant,
                           '--output', str(directory), '--width', str(case['width']), '--height', str(case['height']),
                           '--fps', str(case['fps']), '--frames', str(case['frames']), '--gop', str(case['gop'])]
                if case['codec'] == 'av1':
                    command += ['--aomenc', str(aomenc)]
                if case['bitrate_mbps'] is not None:
                    command += ['--bitrate-mbps', format(case['bitrate_mbps'], '.3f').rstrip('0').rstrip('.')]
                try:
                    with (out / f"{case['name']}-encode.log").open('w') as log:
                        result = run_encoder(command, log, timeout=max(600, timeout))
                except BaseException:
                    # A manifest is the cache's completion marker. Even if an
                    # interrupted process wrote one, it must not be reused.
                    path.unlink(missing_ok=True)
                    raise
                if result.returncode:
                    path.unlink(missing_ok=True)
                    raise ValueError(f"fixture generation failed (exit {result.returncode}); see encode log")
    info, payload = verify_fixture(path, case)
    destination = out / 'fixtures' / info['manifest_sha256']
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(path, destination / 'manifest.json')
    target_payload = destination / info['payload_file']
    target_payload.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(payload, target_payload)
    if requires_reference(info['generator']) and info['generator']['pattern'] != REFERENCE_PATTERN:
        # Lossy compression can erase synthetic source markers. Preserve the
        # encoder's manifest, and require independent full-frame comparison for
        # this derived replay manifest. Compressed payload bytes do not change.
        shutil.copyfile(path, destination / 'source-manifest.json')
        manifest = read_json(path)
        manifest['generator']['pattern'] = REFERENCE_PATTERN
        manifest['correctness_reference'] = dict(method='full-frame-software-comparison',
                                                 source_manifest_sha256=info['manifest_sha256'])
        write_json(destination / 'manifest.json', manifest)
        info, _ = verify_fixture(destination / 'manifest.json', case)
        info['source_manifest'] = str((destination / 'source-manifest.json').relative_to(out))
        info['source_manifest_sha256'] = sha(path)
    elif read_json(path).get('correctness_reference'):
        original = path.parent / 'source-manifest.json'
        declared = read_json(path)['correctness_reference']['source_manifest_sha256']
        if sha(original) != declared or read_json(original)['payload_sha256'] != info['payload_sha256']:
            raise ValueError('imported derived fixture has invalid original encoder provenance')
        shutil.copyfile(original, destination / 'source-manifest.json')
        info['source_manifest'] = str((destination / 'source-manifest.json').relative_to(out))
        info['source_manifest_sha256'] = declared
    info.update(manifest=str((destination / 'manifest.json').relative_to(out)),
                original_manifest=str(path), generation_command=command)
    return info


def replay_command(binary, manifest, prefix, case, run, phase):
    decoder = case['decoder']
    loops = max(1, math.ceil(run['seconds'] * case['fps'] / case['frames'])) if phase == 'timed' else 1
    command = [binary, '--fixture', str(manifest), '--output', str(prefix),
               '--mode', 'paced' if phase == 'timed' else 'correctness',
               '--fps', str(case['fps']), '--loops', str(loops), '--loop-mode', 'continuous',
               '--warmup', str(run['warmup_frames'] if phase == 'timed' else 0)]
    for key, flag in [('inflight', '--inflight'), ('queue_depth', '--queue-depth'),
                      ('power', '--power'), ('consumer_delay_ms', '--consumer-delay-ms'),
                      ('jitter_us', '--jitter-us'), ('seed', '--seed')]:
        command += [flag, str(decoder[key])]
    return command, loops * case['frames']


def invoke(plan, out, case, setting, phase, repetition):
    build = plan['builds'][setting]
    if sha(pathlib.Path(build['binary'])) != build['binary_sha256']:
        raise ValueError(f'{setting} executable changed after preparation')
    manifest = out / case['fixture_info']['manifest']
    info, _ = verify_fixture(manifest, case)
    if info['manifest_sha256'] != case['fixture_info']['manifest_sha256']:
        raise ValueError('fixture manifest changed after preparation')
    relative = pathlib.Path('runs') / case['name'] / f'{phase}-{setting}-{repetition}'
    prefix = out / relative
    prefix.parent.mkdir(parents=True, exist_ok=True)
    command, offered = replay_command(build['binary'], manifest, prefix, case, plan['config']['run'], phase)
    reference = None
    if phase == 'correctness' and requires_reference(info['generator']):
        reference = case.get('reference_info')
        if not reference:
            raise ValueError('noise fixture correctness requires an independent software reference')
        validate_reference(reference, case, out, require_raw=True)
        command += ['--reference-raw', str(out / reference['raw_path'])]
    record = dict(case=case['name'], setting=setting, phase=phase, repetition=repetition,
                  command=command, expected_offered=offered, result_file=str(relative) + '.json',
                  csv_file=str(relative) + '.csv', log_file=str(relative) + '.log',
                  started_at=now(), state='RUNNING', exit_code=None)
    if reference:
        record['reference_raw_sha256'] = reference['raw_sha256']
    plan['runs'].append(record)
    write_json(out / 'plan.json', plan)
    print(f"{phase} {case['name']} {setting} {repetition}", flush=True)
    try:
        with (out / record['log_file']).open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    timeout=plan['config']['run']['timeout_seconds'])
        record['exit_code'] = result.returncode
        record['state'] = 'FINISHED'
    except (OSError, subprocess.TimeoutExpired) as error:
        record.update(state='ERROR', error=str(error))
    record['finished_at'] = now()
    for field in ('result_file', 'csv_file', 'log_file'):
        path = out / record[field]
        record[field + '_sha256'] = sha(path) if path.is_file() else None
    write_json(out / 'plan.json', plan)
    return record


def positive_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    except OverflowError:
        return False


def inspect_run(record, case, out, thresholds):
    item = dict(record)
    errors = []
    try:
        command = record['command']
        if not isinstance(command, list):
            raise ValueError('planned command must be an argument list')
        def argument(flag):
            if command.count(flag) != 1 or command.index(flag) + 1 >= len(command):
                raise ValueError('missing or ambiguous planned argument: ' + flag)
            return command[command.index(flag) + 1]
        planned_warmup = int(argument('--warmup'))
        planned_loops = int(argument('--loops'))
        planned_loop_mode = argument('--loop-mode')
        if (planned_warmup < 0 or planned_loops < 1 or planned_loop_mode != 'continuous'
                or planned_loops * case['frames'] != record['expected_offered']):
            raise ValueError('planned warmup/loop settings are inconsistent')
        if not record.get('result_file_sha256') or sha(out / record['result_file']) != record['result_file_sha256']:
            raise ValueError('result_file missing or changed since execution')
        result = read_json(out / record['result_file'])
        if not isinstance(result, dict) or result.get('status') not in ('PASS', 'FAIL'):
            raise ValueError('missing/invalid native status')
        item['native'] = result
        if result['status'] != 'PASS':
            errors.append('native FAIL: ' + result.get('reason', 'accounting/hardware gate failed'))
        if record['state'] != 'FINISHED' or record['exit_code'] != 0:
            errors.append(f"process {record['state']}, exit {record['exit_code']}")
        # Early native correctness failures may emit only JSON. Keep the
        # verified native diagnosis before rejecting the absent trace; otherwise
        # a useful pixel/format error is hidden behind "CSV missing".
        if not record.get('csv_file_sha256') or sha(out / record['csv_file']) != record['csv_file_sha256']:
            raise ValueError('csv_file missing or changed since execution')
        for key in ('offered', 'submitted', 'completed', 'displayed_outputs', 'scheduler_drops',
                    'rejected', 'failed_or_cancelled_or_dropped', 'expected_display_mismatches', 'trace_overflow', 'resets'):
            if type(result.get(key)) is not int or result[key] < 0:
                raise ValueError('invalid or missing accounting: ' + key)
        if result['offered'] != record['expected_offered']:
            errors.append('offered count differs from planned run')
        if result['submitted'] + result['scheduler_drops'] + result['rejected'] != result['offered']:
            errors.append('offered/admitted accounting mismatch')
        if result['completed'] != result['submitted'] or result['displayed_outputs'] != result['offered']:
            errors.append('not every offered frame produced an output')
        for key in ('scheduler_drops', 'rejected', 'failed_or_cancelled_or_dropped', 'expected_display_mismatches', 'trace_overflow', 'resets'):
            if result[key]:
                errors.append(f'{key}={result[key]}')
        expected = dict(codec=case['codec'], variant='sdr8' if case['dynamic_range'] == 'sdr' else 'hdr10',
                        width=case['width'], height=case['height'], requested_fps=case['fps'],
                        fixture_sha256=case['fixture_info']['payload_sha256'],
                        inflight=case['decoder']['inflight'], power_requested=case['decoder']['power'],
                        consumer_retention_delay_ms=case['decoder']['consumer_delay_ms'],
                        bit_depth=8 if case['dynamic_range'] == 'sdr' else 10, chroma='420',
                        warmup_frames=planned_warmup, loops=planned_loops, loop_mode=planned_loop_mode,
                        steady_excludes_first_output_each_generation=True,
                        mode='paced' if record['phase'] == 'timed' else 'correctness')
        for key, value in expected.items():
            if result.get(key) != value:
                errors.append(f'result {key} differs from plan')
        for key in ('warmup_frames', 'loops'):
            if type(result.get(key)) is not int:
                raise ValueError('invalid or missing run setting: ' + key)
        if result.get('hardware_validated') not in (True, 1):
            errors.append('hardware decoding was not validated')
        with (out / record['csv_file']).open(newline='') as source:
            rows = [{key: int(value) for key, value in row.items()} for row in csv.DictReader(source)]
        if len(rows) != result['submitted'] or len({r['frame_id'] for r in rows}) != len(rows):
            errors.append('CSV completion count/identity mismatch')
        if sum(r['displayed_outputs'] for r in rows) != result['displayed_outputs']:
            errors.append('CSV display count mismatch')
        if any(row['status'] != 0 for row in rows):
            errors.append('CSV contains a non-output terminal completion')
        for row in rows:
            if not 0 <= row['frame_id'] < record['expected_offered']:
                errors.append('CSV frame ID outside planned range')
                break
            if row['status'] == 0 and (row['result'] != 0 or row['hardware'] != 1
                                       or row['bit_depth'] != expected['bit_depth'] or row['displayed_outputs'] != 1):
                errors.append('CSV output failed hardware/format/status validation')
                break
        supplemental = caller_timings(out / record['csv_file'], result)
        item['derived'] = supplemental
        outputs = [row for row in rows if row['status'] == 0 and row['displayed_outputs'] == 1]
        item['first_output_ms'] = ((min(r['sink_entry_ns'] for r in outputs) -
                                    min(r['scheduled_arrival_ns'] for r in rows)) / 1e6) if outputs else None
        if record['phase'] == 'correctness':
            for key in ('correctness_sink', 'iosurface_metal_verified', 'retained_after_destroy_verified'):
                if result.get(key) is not True:
                    errors.append(key + ' was not verified')
            if requires_reference(case['fixture_info'].get('generator', {})):
                reference = case.get('reference_info')
                if not reference:
                    raise ValueError('noise fixture lacks independent software reference evidence')
                validate_reference(reference, case, out)
                if (pathlib.Path(argument('--reference-raw')) != out / reference['raw_path']
                        or record.get('reference_raw_sha256') != reference['raw_sha256']):
                    errors.append('software reference invocation differs from verified reference')
                expected_samples = case['width'] * case['height'] * 3 // 2 * case['frames']
                tolerance = 2 if case['dynamic_range'] == 'sdr' else 8
                if (type(result.get('software_reference_samples')) is not int
                        or result['software_reference_samples'] != expected_samples):
                    errors.append('software reference did not compare every output sample')
                maximum = result.get('software_reference_max_code_error')
                if (type(maximum) not in (int, float) or not 0 <= maximum <= tolerance
                        or result.get('software_reference_tolerance') != tolerance):
                    errors.append('software reference pixel tolerance failed or is missing')
        else:
            if '--reference-raw' in command or result.get('software_reference_samples', 0) != 0:
                errors.append('software reference work must not run during timing')
            if not positive_number(result.get('decoded_fps')):
                raise ValueError('missing/invalid delivered frame rate')
            if result['decoded_fps'] < case['fps'] * thresholds['decoded_fps_ratio']:
                errors.append('delivered frame rate below configured ratio')
            item['metrics'] = {}
            merged = dict(result, **supplemental)
            for name, (field, quantile) in METRICS.items():
                values = merged.get(field)
                if not isinstance(values, dict) or not positive_number(values.get('count')) or not positive_number(values.get(quantile)):
                    raise ValueError('missing/invalid steady latency samples: ' + name)
                item['metrics'][name] = values[quantile] / 1e6
            # Recompute the VT population from the immutable trace, independently
            # of the native aggregate; exclude cold outputs and offered warmup IDs.
            first = {}
            for row in outputs:
                key = row['generation']
                if key not in first or row['frame_id'] < first[key]:
                    first[key] = row['frame_id']
            steady = [r for r in outputs if r['frame_id'] >= planned_warmup
                      and r['frame_id'] != first[r['generation']]]
            # Never let an instrumentation change make the measured population
            # silently smaller. These fixtures promise one genuine image per AU.
            for row in steady:
                if row['internal_samples'] != 1 or row['show_existing']:
                    errors.append('steady output is outside the supported single-sample latency population')
                    break
                if (row['trace_valid'] & 26 != 26
                        or not 0 < row['scheduled_arrival_ns'] <= row['admission_ns'] <= row['vt_submit_ns']
                        <= row['callback_ns'] <= row['sink_entry_ns']):
                    errors.append('steady output has incomplete or invalid VT/public timing trace')
                    break
            vt = [r['callback_ns'] - r['vt_submit_ns'] for r in steady
                  if r['internal_samples'] == 1 and not r['show_existing']
                  and r['trace_valid'] & 10 == 10 and r['callback_ns'] >= r['vt_submit_ns']]
            native = result['vt_submit_to_callback_ns']
            derived = distribution(vt)
            public = supplemental['public_complete_au_to_output_ns']
            if native['count'] != len(steady) or public['count'] != len(steady):
                errors.append('VT/public latency population does not cover every steady output')
            if native['count'] != len(vt) or any(not math.isclose(native[key], derived[key], rel_tol=1e-8, abs_tol=1)
                                                 for key in ('median', 'p95', 'p99')):
                errors.append('native VT latency summary differs from raw CSV')
            item['thermal_nominal'] = type(result.get('thermal_state')) is int and result['thermal_state'] == 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError) as error:
        errors.append('invalid evidence: ' + str(error))
    item['errors'] = errors
    item['passed'] = not errors
    return item


def paired_metrics(baseline, candidate, thresholds):
    comparisons = {}
    for name in METRICS:
        left = [run['metrics'][name] for run in baseline]
        right = [run['metrics'][name] for run in candidate]
        absolute = [new - old for old, new in zip(left, right)]
        relative = [(new / old - 1) * 100 for old, new in zip(left, right)]
        limit = max(thresholds['latency_absolute_ms'],
                    statistics.median(left) * thresholds['latency_relative_pct'] / 100)
        comparisons[name] = dict(baseline_ms=left, candidate_ms=right,
            baseline_median_ms=statistics.median(left), candidate_median_ms=statistics.median(right),
            paired_delta_ms=absolute, paired_delta_pct=relative,
            median_paired_delta_ms=statistics.median(absolute), median_paired_delta_pct=statistics.median(relative),
            allowed_increase_ms=limit, threshold_exceeded=statistics.median(absolute) > limit)
    return comparisons


def analyze(plan, out):
    plan = normalize_plan_bitrates(plan)
    thresholds = plan['config']['thresholds']
    settings = list(plan['builds'])
    cases = []
    for case in plan['cases']:
        fixture_error = None
        archived = None
        try:
            archived, _ = verify_fixture(out / case['fixture_info']['manifest'], case)
            for field in ('manifest_sha256', 'payload_sha256'):
                if archived[field] != case['fixture_info'][field]:
                    raise ValueError('archived fixture ' + field + ' changed after preparation')
            if requires_reference(archived['generator']):
                if not requires_reference(case['fixture_info'].get('generator', {})):
                    raise ValueError('archived noise profile differs from the correctness plan')
                if not case.get('reference_info'):
                    raise ValueError('noise fixture lacks independent software reference evidence')
                validate_reference(case['reference_info'], case, out)
            source = case['fixture_info'].get('source_manifest')
            derivation = read_json(out / case['fixture_info']['manifest']).get('correctness_reference')
            if derivation and (not source or derivation.get('source_manifest_sha256') !=
                               case['fixture_info'].get('source_manifest_sha256')):
                raise ValueError('derived fixture lost original encoder provenance')
            if source:
                original = out / source
                if sha(original) != case['fixture_info']['source_manifest_sha256']:
                    raise ValueError('original encoder manifest changed after preparation')
                if read_json(original)['payload_sha256'] != archived['payload_sha256']:
                    raise ValueError('derived manifest differs from original compressed payload')
        except (OSError, ValueError, TypeError, KeyError, UnicodeError) as error:
            fixture_error = 'fixture evidence invalid: ' + str(error)
        records = [inspect_run(record, case, out, thresholds) for record in plan['runs'] if record['case'] == case['name']]
        requested = case['bitrate_mbps']
        measured = archived['measured_bitrate_mbps'] if archived and not fixture_error else None
        ratio = measured / requested if measured is not None and requested is not None else None
        bitrate_tolerance = thresholds.get('bitrate_tolerance_pct', 20.0)
        coverage_passed = bitrate_covered(requested, measured, bitrate_tolerance)
        report = dict(name=case['name'], settings=case, runs=records, comparisons={}, issues=[],
                      bitrate=dict(requested_mbps=requested, measured_mbps=measured,
                                   measured_to_requested_ratio=ratio, tolerance_pct=bitrate_tolerance,
                                   coverage_passed=coverage_passed))
        expected_runs = {(phase, setting, rep) for setting in settings
                         for phase, reps in [('correctness', [1]), ('timed', range(1, plan['config']['run']['repetitions'] + 1))]
                         for rep in reps}
        unique = {(r['phase'], r['setting'], r['repetition']) for r in records}
        if (case.get('error') or fixture_error or len(records) != len(expected_runs)
                or unique != expected_runs or plan['state'] != 'FINISHED'):
            report.update(status='INCOMPLETE')
            if case.get('error'):
                report['issues'].append(case['error'])
            if fixture_error:
                report['issues'].append(fixture_error)
            if not report['issues']:
                report['issues'].append(plan.get('error', 'not all planned correctness and timed runs completed'))
        else:
            passed = {setting: all(r['passed'] for r in records if r['setting'] == setting) for setting in settings}
            timed = {setting: sorted([r for r in records if r['phase'] == 'timed' and r['setting'] == setting],
                                     key=lambda r: r['repetition']) for setting in settings}
            if 'baseline' in settings and all('metrics' in r and len(r['metrics']) == len(METRICS) for r in records if r['phase'] == 'timed'):
                report['comparisons'] = paired_metrics(timed['baseline'], timed['candidate'], thresholds)
            if 'baseline' in passed and not passed['baseline']:
                report['status'] = 'BASELINE_FAILURE'
                report['issues'].append('baseline failed; latency is descriptive and cannot establish a clean regression result')
            elif not passed['candidate']:
                report['status'] = 'REGRESSION' if 'baseline' in passed else 'FAIL'
            elif requested is not None and coverage_passed is not True:
                report['status'] = 'INCONCLUSIVE'
                report['issues'].append(f'measured payload bitrate {measured:.3f} Mbps is outside '
                    f'the {requested:g} Mbps target ±{bitrate_tolerance:g}%; '
                    'decode checks passed, but requested bitrate coverage was not established')
            elif any(not r.get('thermal_nominal', False) for group in timed.values() for r in group):
                report['status'] = 'INCONCLUSIVE'
                report['issues'].append('non-nominal or unavailable thermal state during timing')
            elif any(value['threshold_exceeded'] for value in report['comparisons'].values()):
                report['status'] = 'REGRESSION'
                report['issues'].append('observed latency increase exceeds the configured threshold; this is not a significance test')
            else:
                report['status'] = 'PASS'
        cases.append(report)
    result = dict(schema_version=1, analyzed_at=now(), analysis_sha256=sha(pathlib.Path(__file__)),
                  status='PASS' if cases and all(c['status'] == 'PASS' for c in cases) else 'FAIL',
                  comparison='paired' if 'baseline' in settings else 'candidate-only',
                  methodology='Alternating baseline/candidate order by repetition and case; identical fixture bytes; '
                    'all correctness gates before serial paced timing; paired differences across repetitions, not pooled frames. '
                    'Configured thresholds are observational gates, not statistical equivalence or significance tests. '
                    'Steady samples exclude offered warmup IDs and first successful output per decoder generation. '
                    'Failures and startup losses remain in accounting. Headless decode does not measure rendering or network.',
                  thresholds=thresholds, builds=plan['builds'], config=plan['config'], cases=cases)
    write_json(out / 'results.json', result)
    report_markdown(result, out / 'report.md')
    suite = ET.Element('testsuite', name='decoder-matrix', tests=str(len(cases)),
                       failures=str(sum(c['status'] != 'PASS' for c in cases)))
    for case in cases:
        test = ET.SubElement(suite, 'testcase', name=case['name'], classname='decoder.hardware')
        if case['status'] != 'PASS':
            failure = ET.SubElement(test, 'failure', type=case['status'], message=case['status'])
            failure.text = '\n'.join(case['issues'] + [f"{r['phase']}/{r['setting']}/{r['repetition']}: {'; '.join(r['errors'])}"
                                                   for r in case['runs'] if r['errors']])
    ET.ElementTree(suite).write(out / 'junit.xml', encoding='utf-8', xml_declaration=True)
    return result


def report_markdown(result, path):
    def number(value):
        return '—' if value is None else f'{value:.3f}'
    run_settings = result['config']['run']
    lines = ['# Decoder comparison', '', f"Overall: **{result['status']}** ({result['comparison']}).", '',
             f"Cases: {len(result['cases'])}; repetitions per build: {run_settings['repetitions']}; "
             f"requested seconds per trial: {run_settings.get('seconds', '—')}; "
             f"warmup offered frames: {run_settings.get('warmup_frames', '—')}.", '', result['methodology'], '',
             'Machine-readable evidence: [results.json](results.json). Bitrates use decimal megabits per second '
             '(1 Mbps = 1,000,000 bits/s). Requested bitrate is an encoder target; measured bitrate is the '
             'encoded payload rate, excluding transport overhead. A clean decode run outside the configured '
             'bitrate tolerance is INCONCLUSIVE for the requested workload.', '',
             '| Case | Result | Requested Mbps | Measured Mbps | Baseline VT median / p95 / p99 ms | Candidate VT median / p95 / p99 ms | Paired median delta |',
             '|---|---|---:|---:|---:|---:|---:|']
    for case in result['cases']:
        metrics = case['comparisons']
        cells = []
        for setting in ('baseline', 'candidate'):
            values = [r for r in case['runs'] if r['phase'] == 'timed' and r['setting'] == setting
                      and all(f'vt_{q}_ms' in r.get('metrics', {}) for q in ('median', 'p95', 'p99'))]
            cells.append(' / '.join(number(statistics.median([r['metrics'][f'vt_{q}_ms'] for r in values])) if values else '—'
                                    for q in ('median', 'p95', 'p99')))
        delta = metrics.get('vt_median_ms', {}).get('median_paired_delta_pct')
        bitrate = case['bitrate']
        requested = 'Default' if bitrate['requested_mbps'] is None else number(bitrate['requested_mbps'])
        lines.append(f"| {case['name']} | {case['status']} | {requested} | {number(bitrate['measured_mbps'])} | "
                     f"{cells[0]} | {cells[1]} | {number(delta)}{'%' if delta is not None else ''} |")
    lines += ['', 'Threshold: the median paired increase must exceed both the absolute allowance '
              f"({result['thresholds']['latency_absolute_ms']} ms) and relative allowance "
              f"({result['thresholds']['latency_relative_pct']}% of baseline median) to flag a latency regression. "
              'Applied independently to VT and public completion median/p95/p99. All output accounting and delivered-rate gates must also pass.', '',
              f"Explicit bitrate targets require measured payload rate within ±{result['thresholds'].get('bitrate_tolerance_pct', 20.0):g}%. "
              'A null target retains the legacy encoder policy and does not impose a bitrate coverage gate.', '',
              'A PASS means the configured gates passed in this sample. It does not prove absence of a smaller regression. '
              'Public latency includes scheduled arrival, queuing and callback delivery; VT latency ends at the internal decoder callback.', '']
    for case in result['cases']:
        lines += [f"## {case['name']}", '', f"Status: {case['status']}", '']
        settings = case['settings']
        reference = settings.get('reference_info')
        if reference is not None:
            reference = reference if isinstance(reference, dict) else {}
            metadata = reference.get('metadata')
            metadata = metadata if isinstance(metadata, dict) else {}
            decoder = metadata.get('decoder')
            decoder = decoder if isinstance(decoder, str) and decoder.strip() else 'unavailable'
            samples = reference.get('expected_samples')
            samples = f'{samples:,}' if type(samples) is int and samples > 0 else 'unavailable'
            checked = [r.get('native', {}) for r in case['runs'] if r['phase'] == 'correctness']
            lines += [f"Full-frame software reference: {decoder}; "
                      f"{samples} samples expected per build; "
                      'observed maximum code errors: ' + ', '.join(str(r.get('software_reference_max_code_error', 'unavailable'))
                                                                  for r in checked) + '.', '']
        ratio = case['bitrate']['measured_to_requested_ratio']
        lines += [f"Stream: {settings['width']}×{settings['height']} at {settings['fps']} fps; "
                  f"{settings['codec'].upper()}, {settings['dynamic_range'].upper()}. "
                  f"Measured bitrate: {number(case['bitrate']['measured_mbps'])} Mbps."
                  + (f" Encoder target: {number(case['bitrate']['requested_mbps'])} Mbps; "
                     f"measured/target: {ratio * 100:.1f}%." if ratio is not None else ''), '']
        if case['issues']:
            lines += case['issues'] + ['']
        for run in case['runs']:
            if run['errors']:
                lines += [f"- {run['phase']} / {run['setting']} / {run['repetition']}: " + '; '.join(run['errors'])]
        if any(run['errors'] for run in case['runs']):
            lines.append('')
        lines += ['| Build / run | Outputs / offered | FPS | Drops / failed | First output ms |', '|---|---:|---:|---:|---:|']
        for run in case['runs']:
            if run['phase'] != 'timed':
                continue
            native = run.get('native', {})
            lines.append(f"| {run['setting']} / {run['repetition']} | {native.get('displayed_outputs', '—')} / {native.get('offered', '—')} | "
                         f"{number(native.get('decoded_fps'))} | {native.get('scheduler_drops', '—')} / "
                         f"{native.get('failed_or_cancelled_or_dropped', '—')} | {number(run.get('first_output_ms'))} |")
        for name, metric in case['comparisons'].items():
            if metric['threshold_exceeded']:
                lines += ['', f"Observed threshold breach: {name}: {metric['median_paired_delta_ms']:+.3f} ms "
                          f"({metric['median_paired_delta_pct']:+.2f}%)."]
        lines.append('')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config')
    parser.add_argument('--candidate-build')
    parser.add_argument('--baseline-build')
    parser.add_argument('--fixture-build')
    parser.add_argument('--reference-tool', help='mav-reference-decode built with MAV_FFMPEG_ROOT; defaults to fixture build')
    parser.add_argument('--candidate-revision')
    parser.add_argument('--baseline-revision')
    parser.add_argument('--aomenc', default=os.environ.get('AOMENC', str(ROOT / '.local/aom-build/aomenc')))
    parser.add_argument('--results-dir')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--prepare-only', action='store_true')
    mode.add_argument('--analyze-only', action='store_true')
    mode.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    if not args.results_dir and not args.dry_run:
        parser.error('--results-dir is required except with --dry-run')
    out = pathlib.Path(args.results_dir).resolve() if args.results_dir else None
    if args.analyze_only:
        result = analyze(read_json(out / 'plan.json'), out)
        return int(result['status'] != 'PASS')
    if not args.config or (not args.candidate_build and not args.dry_run):
        parser.error('--config and --candidate-build are required (--dry-run needs only --config)')
    try:
        config = load_config(args.config)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.dry_run:
        print(json.dumps(config, indent=2))
        return 0
    if out.exists() and any(out.iterdir()):
        parser.error('results directory must be empty; use a new directory to preserve earlier evidence')
    out.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.config, out / 'config.yaml')
    harness = out / 'harness'
    harness.mkdir()
    for name in ('compare-decoders.py', 'benchmark_config.py', 'benchmark_analysis.py',
                 'benchmark_reference.py', 'environment.py', 'requirements-benchmarks.txt'):
        shutil.copyfile(ROOT / 'scripts' / name, harness / name)
    plan = dict(schema_version=1, created_at=now(), state='PREPARING', config=config, builds={},
                cases=[dict(case) for case in config['cases']], runs=[],
                python=sys.version, harness_sha256={p.name: sha(p) for p in harness.iterdir()})
    write_json(out / 'plan.json', plan)
    try:
        for setting in ('baseline', 'candidate'):
            directory = getattr(args, setting + '_build')
            if directory:
                plan['builds'][setting] = build_info(pathlib.Path(directory), setting, getattr(args, setting + '_revision'), out)
        if 'baseline' in plan['builds']:
            if plan['builds']['baseline']['binary_sha256'] == plan['builds']['candidate']['binary_sha256']:
                raise ValueError('baseline and candidate executables are identical; this is not an upgrade comparison')
            left = plan['builds']['baseline']['environment']
            right = plan['builds']['candidate']['environment']
            for key in ('architecture', 'compiler', 'sdk', 'deployment_target'):
                if left[key] != right[key]:
                    raise ValueError('comparison build environments differ: ' + key)
            for key in ('CMAKE_CXX_FLAGS', 'CMAKE_CXX_FLAGS_RELEASE', 'CMAKE_OBJCXX_FLAGS',
                        'CMAKE_OBJCXX_FLAGS_RELEASE', 'CMAKE_OSX_ARCHITECTURES'):
                if left['cmake_cache'].get(key) != right['cmake_cache'].get(key):
                    raise ValueError('comparison build flags differ: ' + key)
        fixture_build = pathlib.Path(args.fixture_build or args.candidate_build).resolve()
        reference_tool = pathlib.Path(args.reference_tool).resolve() if args.reference_tool else fixture_build / 'mav-reference-decode'
        if (not args.prepare_only and any(case['bitrate_mbps'] is not None for case in plan['cases'])
                and (not reference_tool.is_file() or not os.access(reference_tool, os.X_OK))):
            raise ValueError('explicit bitrate fixtures require --reference-tool pointing to mav-reference-decode; '
                             'build it with -DMAV_FFMPEG_ROOT=<FFmpeg development prefix>')
        aomenc = pathlib.Path(args.aomenc).resolve()
        for case in plan['cases']:
            print('prepare ' + case['name'], flush=True)
            try:
                case['fixture_info'] = prepare_fixture(case, fixture_build, aomenc, out, config['run']['timeout_seconds'])
            except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
                case['error'] = str(error)
            write_json(out / 'plan.json', plan)
        plan['state'] = 'PREPARED'
        write_json(out / 'plan.json', plan)
        if args.prepare_only:
            print(f'Prepared {len(plan["cases"])} cases in {out}; no decode runs performed.', flush=True)
            return int(any('error' in case for case in plan['cases']))
        if any('error' in case for case in plan['cases']):
            raise ValueError('fixture preparation failed; no timing is allowed after an encoder/preparation failure')
        plan['state'] = 'RUNNING'
        write_json(out / 'plan.json', plan)
        for case in plan['cases']:
            if 'error' in case:
                continue
            try:
                if requires_reference(case['fixture_info'].get('generator', {})):
                    case['reference_info'] = prepare_reference(reference_tool,
                        out / case['fixture_info']['manifest'], case, out,
                        config['run']['timeout_seconds'], run_encoder)
                    write_json(out / 'plan.json', plan)
                for setting in plan['builds']:
                    record = invoke(plan, out, case, setting, 'correctness', 1)
                    check = inspect_run(record, case, out, config['thresholds'])
                    if not check['passed']:
                        case['error'] = 'correctness gate failed for ' + setting + ': ' + '; '.join(check['errors'])
            except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
                case['error'] = 'correctness preparation failed: ' + str(error)
            finally:
                if case.get('reference_info'):
                    cleanup_reference(case['reference_info'], out)
            write_json(out / 'plan.json', plan)
        for index, case in enumerate(plan['cases']):
            if 'error' in case:
                continue
            for repetition in range(1, config['run']['repetitions'] + 1):
                settings = list(plan['builds'])
                if (index + repetition - 1) % 2:
                    settings.reverse()
                for setting in settings:
                    invoke(plan, out, case, setting, 'timed', repetition)
        plan.update(state='FINISHED', finished_at=now())
    except (OSError, ValueError, KeyError, KeyboardInterrupt) as error:
        plan.update(state='ERROR', error=str(error), finished_at=now())
        print('Comparison stopped: ' + str(error), file=sys.stderr)
    write_json(out / 'plan.json', plan)
    result = analyze(plan, out)
    print(f"{result['status']}: {out / 'report.md'}\nMachine-readable: {out / 'results.json'}", flush=True)
    return int(result['status'] != 'PASS')


if __name__ == '__main__':
    sys.exit(main())
