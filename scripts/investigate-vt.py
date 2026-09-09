#!/usr/bin/env python3
"""Run serial 4K VideoToolbox controls, or reanalyze their saved evidence.

Build and check pixel correctness before timing. Do not run builds, encoders,
profilers, or other benchmarks concurrently. --seconds specifies paced offered
duration; throughput has no arrival clock and uses --throughput-loops. --loops
instead gives both modes the same AU count. These modes remain separate cohorts.
Variants are a JSON object such as {"baseline": {}, "control": {"MAV_VT_X": "1"}}.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import os
import pathlib
import re
import resource
import statistics
import subprocess
import time

from benchmark_analysis import distribution
from environment import capture

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = {f'4k-{codec}-{kind}': f'{codec}-{variant}-3840x2160p60-120'
         for codec in ('av1', 'hevc') for kind, variant in (('sdr', 'sdr8'), ('hdr', 'hdr10'))}
ZERO_FIELDS = ('rejected', 'failed_or_cancelled_or_dropped', 'scheduler_drops',
               'expected_display_mismatches', 'resets', 'trace_overflow', 'no_display', 'show_existing')
TOTAL_FIELDS = ('offered', 'submitted', 'completed', 'displayed_outputs', 'internal_samples')
PHASES = {
    'vt_submit_to_callback_ns': ('callback_ns', 'vt_submit_ns', 10),
    'submission_call_ns': ('vt_return_ns', 'vt_submit_ns', 6),
    'vt_return_to_callback_ns': ('callback_ns', 'vt_return_ns', 14),
    'public_complete_au_to_output_ns': ('sink_entry_ns', 'scheduled_arrival_ns', 24),
    'preparation_ns': ('preparation_end_ns', 'preparation_start_ns', 1),
    'post_parser_to_vt_submit_ns': ('vt_submit_ns', 'preparation_end_ns', 3),
    'callback_to_client_handoff_ns': ('sink_entry_ns', 'callback_ns', 8),
    'queue_wait_ns': ('admission_ns', 'scheduled_arrival_ns', 16),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value, exclusive=False):
    with path.open('x' if exclusive else 'w') as out:
        json.dump(value, out, indent=2, allow_nan=False)
        out.write('\n')


def read_json(path):
    def invalid(value):
        raise ValueError(f'nonfinite JSON number: {value}')
    return json.loads(path.read_text(), parse_constant=invalid)


def variants_from(path):
    variants = read_json(path) if path else {'baseline': {}}
    if not isinstance(variants, dict) or not variants or variants.get('baseline') != {}:
        raise ValueError('variants must include "baseline": {}')
    for name, env in variants.items():
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', name) or not isinstance(env, dict):
            raise ValueError('variant names must be safe filenames and values must be environment objects')
        if any(not re.fullmatch(r'MAV_VT_[A-Z0-9_]+', k) or not isinstance(v, str)
               or '\0' in v for k, v in env.items()):
            raise ValueError('variant controls must be MAV_VT_* keys with string values')
    return variants


def selected(value, allowed, label):
    names = value.split(',')
    if not set(names) <= set(allowed) or len(set(names)) != len(names):
        raise ValueError(f'unknown or duplicate {label}')
    return names


def analyze_trace(rows, result, manifest):
    """Derive signed phase intervals without dropping outcomes from accounting."""
    units = manifest['access_units']
    if not units or [u['frame_id'] for u in units] != list(range(len(units))):
        raise ValueError('fixture frame IDs must be sequential for continuous-loop picture joins')
    outputs = [r for r in rows if r['status'] == 0 and r['displayed_outputs'] == 1]
    first = {}
    for row in outputs:
        first[row['generation']] = min(first.get(row['generation'], row['frame_id']), row['frame_id'])
    steady = [r for r in outputs if r['internal_samples'] == 1 and not r['show_existing']
              and r['frame_id'] >= result['warmup_frames']
              and r['frame_id'] != first[r['generation']]]

    def phases(population):
        return {name: distribution([r[end] - r[start] for r in population
                                   if r['trace_valid'] & mask == mask and r[end] >= r[start]
                                   and (name != 'vt_return_to_callback_ns' or r['vt_return_ns'] >= r['vt_submit_ns'])])
                for name, (end, start, mask) in PHASES.items()}

    metrics = phases(steady)
    eligible = [r for r in steady if r['trace_valid'] & 10 == 10
                and r['callback_ns'] >= r['vt_submit_ns']]
    returns = [r for r in eligible if r['trace_valid'] & 4
               and r['vt_return_ns'] >= r['vt_submit_ns']]
    errors = []
    for metric in ('vt_submit_to_callback_ns', 'preparation_ns', 'submission_call_ns',
                   'callback_to_client_handoff_ns', 'queue_wait_ns'):
        reported = result.get(metric)
        measured = metrics[metric]
        if not isinstance(reported, dict) or reported.get('count') != measured['count']:
            errors.append(f'{metric} count does not match raw CSV')
            continue
        for stat in ('median', 'p95', 'p99'):
            a, b = reported.get(stat), measured[stat]
            if a is None and b is None:
                continue
            if type(a) not in (int, float) or b is None or not math.isfinite(a) or abs(a-b) > 1:
                errors.append(f'{metric} {stat} does not match raw CSV')
    if not steady or metrics['vt_submit_to_callback_ns']['count'] != len(steady):
        errors.append('steady VT timing is empty or incomplete')
    if metrics['public_complete_au_to_output_ns']['count'] != len(steady):
        errors.append('steady public timing is incomplete')
    pictures = {}
    for name, random_access in (('random_access', True), ('inter', False)):
        population = [r for r in steady if units[r['frame_id'] % len(units)]['random_access'] == random_access]
        pictures[name] = dict(rows=len(population), metrics=phases(population),
                             compressed_bytes=distribution([units[r['frame_id'] % len(units)]['length']
                                                            for r in population]))
    return dict(trace_rows=len(rows), steady_rows=len(steady), metrics=metrics, by_picture=pictures,
                callback_before_return_rows=sum(r['callback_ns'] < r['vt_return_ns'] for r in returns),
                missing_or_invalid_return_rows=len(eligible)-len(returns), errors=errors)


def analyze_run(directory, invocation, fixture):
    record = dict(invocation, qualified=False, errors=[])
    errors = record['errors']
    try:
        diagnostics = []
        stderr = directory / invocation.get('stderr_file', 'missing.stderr.log')
        if stderr.is_file():
            for line in stderr.read_text(errors='replace').splitlines():
                if line.startswith('MAV_VT_EXPERIMENT '):
                    try:
                        diagnostics.append(json.loads(line[len('MAV_VT_EXPERIMENT '):]))
                    except ValueError:
                        errors.append('malformed MAV_VT_EXPERIMENT diagnostic')
        record['experiment_diagnostics'] = diagnostics
        record['control_interpretation'] = ('Environment records requested controls; consult experiment diagnostics '
            'for property setter/support/readback and actual output. PASS alone does not prove a control applied.')
        for artifact, expected in invocation['artifact_sha256'].items():
            if digest(directory / artifact) != expected:
                errors.append(f'artifact hash mismatch: {artifact}')
        result = read_json(directory / invocation['result_file'])
        if not isinstance(result, dict):
            raise ValueError('result must be a JSON object')
        record['result'] = result
        if invocation['exit_code'] != 0 or result.get('status') != 'PASS':
            errors.append('replay process or reported result failed')
        for field in TOTAL_FIELDS:
            if type(result.get(field)) is not int or result[field] != invocation['expected_frames']:
                errors.append(f'{field} does not equal expected frames')
        for field in ZERO_FIELDS:
            if type(result.get(field)) is not int or result[field] != 0:
                errors.append(f'{field} is missing or nonzero')
        if result.get('hardware_validated') != 1:
            errors.append('hardware decoding was not verified')
        manifest = fixture['document']
        for field in ('codec', 'variant', 'width', 'height', 'bit_depth', 'chroma'):
            if result.get(field) != manifest[field]:
                errors.append(f'result fixture format mismatch: {field}')
        if result.get('fixture_sha256') != fixture['payload_sha256']:
            errors.append('result fixture hash mismatch')
        for field in ('mode', 'loops', 'warmup_frames', 'inflight'):
            if result.get(field) != invocation[field]:
                errors.append(f'result invocation mismatch: {field}')
        if result.get('loop_mode') != 'continuous':
            errors.append('session is not continuous')
        with (directory / invocation['csv_file']).open(newline='') as source:
            rows = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(source)]
        ids = [r['frame_id'] for r in rows]
        if len(rows) != result.get('completed') or sorted(ids) != list(range(invocation['expected_frames'])):
            errors.append('CSV count, duplicate IDs, or missing completion IDs')
        for row in rows:
            if (row['status'] != 0 or row['displayed_outputs'] != 1 or row['hardware'] != 1
                    or row['internal_samples'] != 1 or row['show_existing'] != 0
                    or row['bit_depth'] != manifest['bit_depth'] or row['pixel_format'] != result.get('pixel_format')):
                errors.append('CSV has failed, nonhardware, wrong-format, or unexpected output')
                break
        record['phases'] = analyze_trace(rows, result, manifest)
        errors.extend(record['phases']['errors'])
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as error:
        errors.append(f'{type(error).__name__}: {error}')
    record['qualified'] = not errors
    return record


def analyze(directory):
    summary = read_json(directory / 'summary.json')
    records, identities = [], set()
    for run in summary['runs']:
        identity = (run['case'], run['variant'], run['mode'], run['repetition'])
        if identity in identities:
            raise ValueError('duplicate run identity in saved summary')
        identities.add(identity)
        records.append(analyze_run(directory, run, summary['fixtures'][run['case']]))
    groups = collections.defaultdict(list)
    for run in records:
        groups[(run['case'], run['variant'], run['mode'])].append(run)
    aggregates = []
    for (case, variant, mode), runs in groups.items():
        passing = [r for r in runs if r['qualified']]
        complete = len(runs) == summary['repetitions'] and len(passing) == len(runs)
        # No aggregate speed claim from a failed, partial, or interrupted cohort.
        metrics = {}
        if complete:
            for metric in PHASES:
                values = [r['phases']['metrics'][metric] for r in passing]
                if all(v['count'] for v in values):
                    metrics[metric] = {stat: statistics.median(v[stat] for v in values)
                                       for stat in ('median', 'p95', 'p99')}
                    metrics[metric]['per_run_counts'] = [v['count'] for v in values]
        aggregates.append(dict(case=case, variant=variant, mode=mode, runs=len(runs),
                               qualified_runs=len(passing), cohort_qualified=complete, metrics=metrics))
    return dict(schema_version=1, metadata={k: v for k, v in summary.items() if k != 'runs'},
                runs=records, aggregates=aggregates,
                interpretation='Nanoseconds. Medians of per-run percentiles, not pooled; phases are not additive. '
                'Only complete passing cohorts receive aggregate timings. Individual failed-run timings are diagnostic. '
                'Cold and warmup excluded only from timing, never outcomes. VT includes API, driver, decode and '
                'callback dispatch. Throughput is not paced latency; hardware-only and Qt/presentation times are unmeasured.')


def run(args):
    cases = selected(args.cases, CASES, 'cases')
    modes = selected(args.modes, ('paced', 'throughput'), 'modes')
    variants = variants_from(args.variants)
    binary = args.binary.resolve()
    if not binary.is_file():
        raise ValueError(f'missing binary: {binary}')
    directory = args.results_dir.resolve()
    if directory.exists():
        raise ValueError('results directory already exists; choose a new directory to preserve evidence')
    if not 1 <= args.repetitions <= 20 or not 0 <= args.warmup <= 100000:
        raise ValueError('repetitions must be 1..20; warmup must be 0..100000')
    if not 1 <= args.inflight <= 16 or not 1 <= args.queue_depth <= 4096:
        raise ValueError('inflight must be 1..16; queue-depth must be 1..4096')
    if args.seconds is not None and (not math.isfinite(args.seconds) or not 0 < args.seconds <= 600):
        raise ValueError('seconds must be positive and at most 600')
    fixtures = {}
    for case in cases:
        manifest = ROOT / 'fixtures/generated' / CASES[case] / 'manifest.json'
        document = read_json(manifest)
        payload = (manifest.parent / document['payload_file']).resolve()
        if not payload.is_relative_to(manifest.parent.resolve()) or digest(payload) != document['payload_sha256']:
            raise ValueError(f'fixture payload path/hash mismatch: {case}')
        if (document['width'], document['height'], document['frame_rate']) != (3840, 2160, {'num': 60, 'den': 1}):
            raise ValueError(f'fixture is not 4K60: {case}')
        if any(u['expected_display_count'] != 1 for u in document['access_units']):
            raise ValueError('this screen requires one display per AU')
        fixtures[case] = dict(manifest=str(manifest), manifest_sha256=digest(manifest), payload=str(payload),
                              payload_sha256=document['payload_sha256'], document=document)
        for mode in modes:
            loops = args.loops if args.loops is not None else (args.throughput_loops if mode == 'throughput'
                    else math.ceil((args.seconds or 10) * 60 / len(document['access_units'])))
            frames = loops * len(document['access_units'])
            if not 1 <= loops <= 10000 or not args.warmup < frames <= 1000000:
                raise ValueError('loops must be 1..10000 and warmup < offered frames <= 1000000')
    directory.mkdir(parents=True)
    environment = capture(args.source_dir.resolve(), binary.parent, directory / 'environment.json')
    if environment['build_type'] != 'Release':
        raise ValueError('timing requires a Release build with an adjacent CMakeCache.txt')
    # Exact, minimal child environment; inherited experimental controls cannot contaminate baseline.
    base_env = {k: os.environ[k] for k in ('HOME', 'TMPDIR', 'LANG', 'LC_ALL') if k in os.environ}
    base_env['PATH'] = os.environ.get('PATH', os.defpath)
    summary = dict(schema_version=1, binary=str(binary), binary_sha256=digest(binary), environment=environment,
                   source_dir=str(args.source_dir.resolve()),
                   runner_sha256=digest(pathlib.Path(__file__)), fixtures=fixtures, variants=variants,
                   repetitions=args.repetitions, runs=[], planned_runs=len(cases)*len(modes)*len(variants)*args.repetitions,
                   ordering='Serial per case; rotate combined variant/mode order each repetition.',
                   duration_semantics='Seconds set paced offered duration; throughput uses loops. Explicit loops set both counts.',
                   correctness='Run equivalent-pixel correctness separately before using these timings.')
    write_json(directory / 'summary.json', summary)
    combinations = [(variant, mode) for variant in variants for mode in modes]
    for case in cases:
        fixture = fixtures[case]
        for rep in range(args.repetitions):
            shift = rep % len(combinations)
            for variant, mode in combinations[shift:] + combinations[:shift]:
                if digest(binary) != summary['binary_sha256'] or digest(pathlib.Path(fixture['manifest'])) != fixture['manifest_sha256'] or digest(pathlib.Path(fixture['payload'])) != fixture['payload_sha256']:
                    raise ValueError('binary or fixture changed during investigation')
                units = len(fixture['document']['access_units'])
                loops = args.loops if args.loops is not None else (args.throughput_loops if mode == 'throughput'
                        else math.ceil((args.seconds or 10) * 60 / units))
                prefix = f'{case}-{variant}-{mode}-rep{rep+1}'
                command = list(map(str, [binary, '--fixture', fixture['manifest'], '--mode', mode, '--fps', 60,
                    '--loops', loops, '--loop-mode', 'continuous', '--warmup', args.warmup,
                    '--inflight', args.inflight, '--queue-depth', args.queue_depth, '--output', directory / prefix]))
                child_env = dict(base_env, **variants[variant])
                invocation = dict(case=case, variant=variant, mode=mode, repetition=rep+1, loops=loops,
                    warmup_frames=args.warmup, inflight=args.inflight, queue_depth=args.queue_depth,
                    expected_frames=loops*units, command=command, cwd=str(ROOT), environment=child_env,
                    result_file=prefix+'.json', csv_file=prefix+'.csv', stdout_file=prefix+'.stdout.log',
                    stderr_file=prefix+'.stderr.log', exit_code=None, artifact_sha256={})
                summary['runs'].append(invocation)
                write_json(directory / 'summary.json', summary)
                print(f'START {prefix}', flush=True)
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                start = time.monotonic()
                with (directory / invocation['stdout_file']).open('x') as stdout, (directory / invocation['stderr_file']).open('x') as stderr:
                    process = subprocess.run(command, cwd=ROOT, env=child_env, stdout=stdout, stderr=stderr)
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                invocation.update(exit_code=process.returncode, process_wall_seconds=time.monotonic()-start,
                                  process_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
                for field in ('result_file', 'csv_file', 'stdout_file', 'stderr_file'):
                    artifact = invocation[field]
                    if (directory / artifact).is_file():
                        invocation['artifact_sha256'][artifact] = digest(directory / artifact)
                write_json(directory / 'summary.json', summary)
                outcome = analyze_run(directory, invocation, fixture)
                print(f"RESULT {prefix}: {'QUALIFIED' if outcome['qualified'] else 'FAILED'}", flush=True)
    evidence = analyze(directory)
    write_json(directory / 'evidence.json', evidence, exclusive=True)
    return int(any(not r['qualified'] for r in evidence['runs']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', type=pathlib.Path, help='reanalyze an existing result directory; never executes replay')
    parser.add_argument('--output', type=pathlib.Path, help='new portable analysis JSON path')
    parser.add_argument('--binary', type=pathlib.Path, default=ROOT / 'build/mav-replay')
    parser.add_argument('--source-dir', type=pathlib.Path, default=ROOT, help='source tree corresponding to the selected binary')
    parser.add_argument('--results-dir', type=pathlib.Path)
    parser.add_argument('--cases', default=','.join(CASES))
    parser.add_argument('--modes', default='paced,throughput')
    duration = parser.add_mutually_exclusive_group()
    duration.add_argument('--seconds', type=float)
    duration.add_argument('--loops', type=int)
    parser.add_argument('--throughput-loops', type=int, default=100)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--warmup', type=int, default=120)
    parser.add_argument('--inflight', type=int, default=2)
    parser.add_argument('--queue-depth', type=int, default=32)
    parser.add_argument('--variants', type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        if args.analyze:
            if args.results_dir:
                raise ValueError('--analyze and --results-dir are mutually exclusive')
            output = args.output or args.analyze / 'reanalysis.json'
            evidence = analyze(args.analyze)
            write_json(output, evidence, exclusive=True)
            return int(not evidence['runs'] or len(evidence['runs']) != evidence['metadata']['planned_runs']
                       or any(not r['qualified'] for r in evidence['runs']))
        if not args.results_dir or args.output:
            raise ValueError('run mode requires --results-dir; --output is only for --analyze')
        return run(args)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
