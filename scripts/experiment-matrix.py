#!/usr/bin/env python3
"""Run isolated decoder experiments serially with shared saved fixtures.

Build, encode and validate before using --phase timed. Never run concurrent
benchmarks, encoders or builds on the device while this runner is active.
"""
import argparse
import hashlib
import json
import math
import pathlib
import resource
import subprocess
import time

from environment import capture

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = {
    '1080-av1-sdr': ('av1-sdr8-1920x1080p120-120', 120),
    '1080-hevc-sdr': ('hevc-sdr8-1920x1080p120-120', 120),
    '4k-av1-sdr': ('av1-sdr8-3840x2160p60-120', 60),
    '4k-av1-hdr': ('av1-hdr10-3840x2160p60-120', 60),
    '4k-hevc-sdr': ('hevc-sdr8-3840x2160p60-120', 60),
    '4k-hevc-hdr': ('hevc-hdr10-3840x2160p60-120', 60),
    'ultrawide-av1-hdr': ('av1-hdr10-3440x1440p240-240', 240),
}
# Name -> worktree suffix (None is unchanged baseline), arguments, codec filter.
SETTINGS = {
    'baseline': (None, [], None),
    'qos-default': ('qos', ['--qos', 'unchanged'], None),
    'qos-initiated': ('qos', ['--qos', 'user-initiated'], None),
    'qos-interactive': ('qos', ['--qos', 'user-interactive'], None),
    'dispatch-async': ('vt-sync', ['--vt-mode', 'asynchronous'], None),
    'dispatch-sync': ('vt-sync', ['--vt-mode', 'synchronous'], None),
    'pacing-sleep': ('pacing', ['--spin-us', '0'], None),
    'pacing-250': ('pacing', ['--spin-us', '250'], None),
    'pacing-1000': ('pacing', ['--spin-us', '1000'], None),
    'hevc-scan': ('hevc-scan', [], 'hevc'),
    'parser-state': ('parser-state', [], None),
    'pool-0': ('cold-start', ['--pool-minimum', '0'], None),
    'pool-3': ('cold-start', ['--pool-minimum', '3'], None),
    'pool-6': ('cold-start', ['--pool-minimum', '6'], None),
    'direct-0': ('direct-session', ['--skip-capability', '0', '--pool-minimum', '0'], None),
    'direct-1': ('direct-session', ['--skip-capability', '1', '--pool-minimum', '0'], None),
}


def read_result(path):
    """Validate the result fields used by the runner without altering evidence."""
    result = json.loads(path.read_text())
    if not isinstance(result, dict) or result.get('status') not in ('PASS', 'FAIL'):
        raise ValueError('result must be a JSON object with PASS or FAIL status')
    timing = result.get('vt_submit_to_callback_ns')
    if timing is not None:
        if not isinstance(timing, dict):
            raise ValueError('vt_submit_to_callback_ns must be an object or null')
        median = timing.get('median')
        if median is not None and (type(median) not in (int, float) or not math.isfinite(median)):
            raise ValueError('VT median must be a finite number or null')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['correctness', 'timed', 'cold'], required=True)
    parser.add_argument('--cases', default=','.join(k for k in CASES if not k.startswith('ultrawide')))
    parser.add_argument('--settings', default=','.join(k for k in SETTINGS if not k.startswith(('pool-', 'direct-'))))
    parser.add_argument('--seconds', type=int, default=10)
    parser.add_argument('--repetitions', type=int, default=3)
    parser.add_argument('--queue-depth', type=int, default=32)
    parser.add_argument('--results-dir', required=True)
    args = parser.parse_args()
    cases = args.cases.split(',')
    settings = args.settings.split(',')
    if not set(cases) <= CASES.keys() or not set(settings) <= SETTINGS.keys():
        parser.error('unknown case or setting')
    if len(set(cases)) != len(cases) or len(set(settings)) != len(settings):
        parser.error('duplicate cases/settings would overwrite evidence')
    if not any(SETTINGS[s][2] in (None, c.split('-')[1]) for c in cases for s in settings):
        parser.error('no selected setting applies to the selected codecs')
    if not 4 <= args.seconds <= 120 or not 1 <= args.repetitions <= 10:
        parser.error('seconds must be 4..120; repetitions must be 1..10')
    if not 1 <= args.queue_depth <= 4096:
        parser.error('queue depth must be 1..4096')
    directory = ROOT / args.results_dir
    if directory.exists() and any(directory.iterdir()):
        parser.error('results directory is not empty; preserve prior evidence in another directory')
    directory.mkdir(parents=True, exist_ok=True)
    environments = {}
    for name in settings:
        suffix, _, _ = SETTINGS[name]
        source = ROOT / 'build-experiments' / f'wt-{suffix}' if suffix else ROOT
        binary = source / 'build/mav-replay'
        if not binary.is_file():
            parser.error(f'missing built binary for {name}: {binary}')
        if str(source) not in environments:
            environment = capture(source, source / 'build', directory / f'environment-{suffix or "baseline"}.json')
            if environment['build_type'] != 'Release':
                parser.error(f'{name} is not a Release build')
            environments[str(source)] = environment
    fixtures = {}
    for case in cases:
        manifest = ROOT / 'fixtures/generated' / CASES[case][0] / 'manifest.json'
        document = json.loads(manifest.read_text())
        fixtures[case] = dict(manifest=str(manifest), manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                              payload_sha256=document['payload_sha256'], units=len(document['access_units']))
    summary = dict(schema_version=1, phase=args.phase, seconds_requested=args.seconds,
                   repetitions=args.repetitions, queue_depth=args.queue_depth, inflight=2, warmup=120,
                   environments=environments, fixtures=fixtures, runs=[],
                   ordering='For each case, rotate setting order each repetition. Two-setting comparisons alternate order; runs are serial.',
                   cpu_semantics='Child process CPU delta includes fixture loading and result serialization; pacing branch also records timed process CPU.',
                   production_defaults_changed=False)
    def save():
        (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    save()
    for case in cases:
        _, fps = CASES[case]
        fixture = fixtures[case]
        codec = case.split('-')[1]
        applicable = [s for s in settings if SETTINGS[s][2] in (None, codec)]
        if not applicable:
            continue
        repetitions = args.repetitions if args.phase in ('timed', 'cold') else 1
        for repetition in range(repetitions):
            order = applicable[repetition % len(applicable):] + applicable[:repetition % len(applicable)]
            for name in order:
                suffix, extra, _ = SETTINGS[name]
                source = ROOT / 'build-experiments' / f'wt-{suffix}' if suffix else ROOT
                binary = source / 'build/mav-replay'
                assert hashlib.sha256(binary.read_bytes()).hexdigest() == environments[str(source)]['binaries']['mav-replay'], 'binary changed during experiment'
                assert hashlib.sha256(pathlib.Path(fixture['manifest']).read_bytes()).hexdigest() == fixture['manifest_sha256'], 'fixture manifest changed during experiment'
                prefix = directory / f'{case}-{name}-rep{repetition+1}'
                if suffix in ('cold-start', 'direct-session'):
                    extra = [*extra, '--cold-trace', str(prefix) + '.cold.jsonl']
                mode = {'timed': 'paced', 'cold': 'throughput', 'correctness': 'correctness'}[args.phase]
                loops = math.ceil(args.seconds * fps / fixture['units']) if args.phase == 'timed' else 1
                command = list(map(str, [binary, '--fixture', fixture['manifest'], '--mode', mode, '--fps', fps,
                                        '--loops', loops, '--loop-mode', 'continuous', '--warmup', 120,
                                        '--inflight', 2, '--queue-depth', args.queue_depth, '--output', prefix, *extra]))
                print(f'START {case} {name} rep{repetition+1}', flush=True)
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                start = time.monotonic()
                with prefix.with_suffix('.log').open('w') as log:
                    process = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                wall_seconds = time.monotonic() - start
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                run = dict(case=case, setting=name, repetition=repetition+1, command=command,
                           exit_code=process.returncode, result_file=str(prefix.with_suffix('.json')),
                           process_wall_seconds=wall_seconds,
                           process_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime)
                summary['runs'].append(run)
                # Persist the completed invocation before touching potentially partial output.
                save()
                try:
                    result = read_result(prefix.with_suffix('.json'))
                except (OSError, UnicodeError, ValueError, OverflowError) as error:
                    run['result_error'] = f'{type(error).__name__}: {error}'
                    result = dict(status='MISSING_OR_INVALID_RESULT')
                run['result_status'] = result['status']
                save()
                vt = result.get('vt_submit_to_callback_ns') or {}
                median = vt.get('median')
                print(f"RESULT {case} {name} {result.get('status', 'ERROR')} "
                      f"{result.get('displayed_outputs')}/{result.get('offered')} "
                      f"VT p50={median/1e6 if median is not None else None} ms", flush=True)
                if args.phase == 'correctness' and (process.returncode or run['result_status'] != 'PASS'):
                    raise RuntimeError(f'correctness failed: {prefix.with_suffix(".log")}')
    return int(any(r['exit_code'] or r['result_status'] != 'PASS' for r in summary['runs']))


if __name__ == '__main__':
    raise SystemExit(main())
