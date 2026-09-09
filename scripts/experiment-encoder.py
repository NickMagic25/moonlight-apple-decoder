#!/usr/bin/env python3
"""Decode saved layout fixtures serially; encoding is a separate prerequisite."""
import argparse
import hashlib
import json
import math
import pathlib
import subprocess

from environment import capture

ROOT = pathlib.Path(__file__).resolve().parents[1]


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
    parser.add_argument('--phase', choices=['correctness', 'timed'], required=True)
    parser.add_argument('--plan', default='results/experiment-preparation/encoder-plan.json')
    parser.add_argument('--results-dir', required=True)
    parser.add_argument('--seconds', type=int, default=10)
    parser.add_argument('--repetitions', type=int, default=3)
    args = parser.parse_args()
    if not 4 <= args.seconds <= 120 or not 1 <= args.repetitions <= 10:
        parser.error('seconds must be 4..120 and repetitions 1..10')
    directory = ROOT / args.results_dir
    if directory.exists() and any(directory.iterdir()):
        parser.error('results directory is not empty')
    directory.mkdir(parents=True, exist_ok=True)
    environment = capture(ROOT, ROOT / 'build', directory / 'environment.json')
    if environment['build_type'] != 'Release':
        parser.error('Release build required')
    groups, fixtures = {}, {}
    for item in json.loads((ROOT / args.plan).read_text())['commands']:
        case, setting = item['case'], f"columns{item['tile_columns_log2']}"
        manifest = pathlib.Path(item['fixture'])
        document = json.loads(manifest.read_text())
        fixture_id = f'{case}-{setting}'
        if fixture_id in fixtures:
            parser.error('duplicate fixture would overwrite evidence')
        fixtures[fixture_id] = dict(manifest=str(manifest), manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
                                   payload_sha256=document['payload_sha256'], units=len(document['access_units']),
                                   fps=document['frame_rate']['num']/document['frame_rate']['den'])
        groups.setdefault(case, []).append((setting, fixture_id))
    summary = dict(schema_version=1, phase=args.phase, seconds_requested=args.seconds,
                   repetitions=args.repetitions, inflight=2, queue_depth=32, warmup=120,
                   environments={str(ROOT): environment}, fixtures=fixtures, runs=[],
                   ordering='Rotate tile-setting order per repetition; three repetitions place each setting once in each position; serial runs.',
                   interpretation='Fixed CQ/source/settings except tile columns; consult separate bitrate, PSNR and actual geometry evidence.')
    def save():
        (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    save()
    for case, settings in groups.items():
        for repetition in range(args.repetitions if args.phase == 'timed' else 1):
            order = settings[repetition % len(settings):] + settings[:repetition % len(settings)]
            for setting, fixture_id in order:
                fixture = fixtures[fixture_id]
                assert hashlib.sha256((ROOT / 'build/mav-replay').read_bytes()).hexdigest() == environment['binaries']['mav-replay']
                assert hashlib.sha256(pathlib.Path(fixture['manifest']).read_bytes()).hexdigest() == fixture['manifest_sha256']
                prefix = directory / f'{case}-{setting}-rep{repetition+1}'
                loops = math.ceil(args.seconds * fixture['fps'] / fixture['units']) if args.phase == 'timed' else 1
                command = list(map(str, [ROOT / 'build/mav-replay', '--fixture', fixture['manifest'],
                                        '--mode', 'paced' if args.phase == 'timed' else 'correctness',
                                        '--fps', fixture['fps'], '--loops', loops, '--loop-mode', 'continuous',
                                        '--warmup', 120, '--inflight', 2, '--queue-depth', 32, '--output', prefix]))
                print(f'START {case} {setting} rep{repetition+1}', flush=True)
                with prefix.with_suffix('.log').open('w') as log:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=ROOT)
                run = dict(case=case, setting=setting, fixture_id=fixture_id, repetition=repetition+1,
                           command=command, exit_code=result.returncode, result_file=str(prefix.with_suffix('.json')))
                summary['runs'].append(run)
                # Persist the completed invocation before touching potentially partial output.
                save()
                try:
                    record = read_result(prefix.with_suffix('.json'))
                except (OSError, UnicodeError, ValueError, OverflowError) as error:
                    run['result_error'] = f'{type(error).__name__}: {error}'
                    record = dict(status='MISSING_OR_INVALID_RESULT')
                run['result_status'] = record['status']
                save()
                median = (record.get('vt_submit_to_callback_ns') or {}).get('median')
                print(f"RESULT {case} {setting} {record.get('status', 'ERROR')} "
                      f"{record.get('displayed_outputs')}/{record.get('offered')} VT p50={median/1e6 if median else None} ms", flush=True)
                if args.phase == 'correctness' and (result.returncode or run['result_status'] != 'PASS'):
                    raise RuntimeError(f'correctness failed: {prefix.with_suffix(".log")}')
    return int(any(run['exit_code'] or run['result_status'] != 'PASS' for run in summary['runs']))


if __name__ == '__main__':
    raise SystemExit(main())
