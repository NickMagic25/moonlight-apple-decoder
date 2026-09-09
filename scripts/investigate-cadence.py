#!/usr/bin/env python3
"""Compare saturated and paced decode with one existing Release binary.

No build, encoder, pixel-validation worker or profiling runs during timing.
Saturated timings are diagnostic and do not establish latency at the paced rate.
"""
import argparse
import csv
import hashlib
import json
import pathlib
import subprocess

from benchmark_analysis import caller_timings, distribution
from environment import capture

ROOT = pathlib.Path(__file__).resolve().parents[1]
CASES = [
    ('av1-sdr8-1920x1080p120-120', 120, 100),
    ('hevc-sdr8-1920x1080p120-120', 120, 100),
    ('av1-hdr10-3440x1440p240-240', 240, 30),
]


def summarize(directory, destination):
    runs = []
    for invocation in json.loads((directory / 'summary.json').read_text()):
        path = pathlib.Path(invocation['result'])
        result = json.loads(path.read_text())
        manifest_path = ROOT / 'fixtures/generated' / invocation['case'] / 'manifest.json'
        manifest = json.loads(manifest_path.read_text())
        if manifest['payload_sha256'] != result['fixture_sha256']:
            raise ValueError(f'fixture changed since the recorded run: {manifest_path}')
        if any(manifest[key] != result[key] for key in ('codec', 'variant', 'width', 'height', 'bit_depth')):
            raise ValueError(f'fixture description disagrees with recorded run: {manifest_path}')
        if invocation['mode'] != result['mode']:
            raise ValueError(f'invocation mode disagrees with recorded run: {path}')
        units = manifest['access_units']
        # These generated fixtures have dense IDs and one displayed sample/AU.
        assert [u['frame_id'] for u in units] == list(range(len(units)))
        with path.with_suffix('.csv').open(newline='') as source:
            rows = [{k: int(v) for k, v in r.items()} for r in csv.DictReader(source)]
        first = {}
        for row in rows:
            if row['status'] == 0:
                first[row['generation']] = min(first.get(row['generation'], row['frame_id']), row['frame_id'])
        steady = [r for r in rows if r['status'] == 0 and r['displayed_outputs'] == 1
                  and r['internal_samples'] == 1 and not r['show_existing']
                  and r['frame_id'] >= result['warmup_frames']
                  and r['frame_id'] != first[r['generation']]
                  and r['trace_valid'] & 10 == 10 and r['callback_ns'] >= r['vt_submit_ns']]
        vt = distribution([r['callback_ns'] - r['vt_submit_ns'] for r in steady])
        # Independently reproduce the harness distribution before deriving phases.
        assert vt['count'] == result['vt_submit_to_callback_ns']['count']
        for key in ('median', 'p95', 'p99'):
            assert abs(vt[key] - result['vt_submit_to_callback_ns'][key]) < 1
        paired = [r for r in steady if r['trace_valid'] & 4
                  and r['vt_submit_ns'] <= r['vt_return_ns'] <= r['callback_ns']]
        phases = dict(
            steady_rows=len(steady), ordered_return_rows=len(paired),
            missing_or_nonordered_return_rows=len(steady)-len(paired),
            vt_call_ns=distribution([r['vt_return_ns']-r['vt_submit_ns'] for r in paired]),
            vt_return_to_callback_ns=distribution([r['callback_ns']-r['vt_return_ns'] for r in paired]),
            paired_vt_submit_to_callback_ns=distribution([r['callback_ns']-r['vt_submit_ns'] for r in paired]),
        )
        by_picture = {}
        for name, random_access in [('random_access', True), ('inter', False)]:
            selected = [r for r in steady if units[r['frame_id'] % len(units)]['random_access'] == random_access]
            by_picture[name] = dict(
                vt_submit_to_callback_ns=distribution([r['callback_ns']-r['vt_submit_ns'] for r in selected]),
                preparation_ns=distribution([r['preparation_end_ns']-r['preparation_start_ns']
                                             for r in selected if r['trace_valid'] & 1]),
                compressed_bytes=distribution([units[r['frame_id'] % len(units)]['length'] for r in selected]),
            )
        result.update(caller_timings(path.with_suffix('.csv'), result))
        run = dict(invocation)
        run['result_file'] = run.pop('result')
        runs.append(dict(
            **run, result=result, phases=phases, by_picture=by_picture,
            scheduler_queue_depth=32,
            raw_csv_sha256=hashlib.sha256(path.with_suffix('.csv').read_bytes()).hexdigest(),
            manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        ))
    document = dict(
        schema_version=1, headless_only=True,
        environment=json.loads((directory / 'environment.json').read_text()),
        method='Three repetitions per case/mode, alternating mode order. Same binary and compressed bytes; '
               'continuous sessions, in-flight 2, queue depth 32, warmup 120. Paced: 10 loops. '
               'Throughput: 100 loops at 1080p, 30 ultrawide; actual offered rate is unrestricted. '
               'No pixel-validation worker in either mode. All original accounting is preserved.',
        interpretation='The throughput/paced difference includes cadence, occupancy and scheduling effects. '
                       'VT callback entry is not a hardware-only timer. This does not establish sub-1-ms paced decode. '
                       'Phase distributions use only rows with valid ordered return timestamps; percentiles are not additive.',
        runs=runs,
    )
    encoded = json.dumps(document, indent=2).replace(str(ROOT), '$REPO')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(encoded + '\n')
    print(f'Preserved {len(runs)} runs in {destination.relative_to(ROOT)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', default='results/optimization-cadence')
    parser.add_argument('--output', default='docs/evidence/optimization-cadence.json')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()
    directory = ROOT / args.results_dir
    if not args.analyze_only:
        # Preserve evidence; use a new --results-dir for another experiment.
        if directory.exists() and any(directory.iterdir()):
            parser.error('results directory is not empty; choose a new directory or --analyze-only')
        for case, _, _ in CASES:
            if not (ROOT / 'fixtures/generated' / case / 'manifest.json').is_file():
                parser.error(f'missing fixture: {case}')
        directory.mkdir(parents=True, exist_ok=True)
        capture(ROOT, ROOT / 'build', directory / 'environment.json')
        invocations = []
        for case, fps, throughput_loops in CASES:
            for repetition in range(1, 4):
                modes = ['throughput', 'paced'] if repetition % 2 else ['paced', 'throughput']
                for mode in modes:
                    output = directory / f'{case}-{mode}-rep{repetition}'
                    command = ['build/mav-replay', '--fixture', str(ROOT / 'fixtures/generated' / case / 'manifest.json'),
                               '--mode', mode, '--fps', str(fps), '--loops', str(10 if mode == 'paced' else throughput_loops),
                               '--loop-mode', 'continuous', '--inflight', '2', '--queue-depth', '32', '--warmup', '120',
                               '--output', str(output)]
                    print(f'START {case} {mode} {repetition}', flush=True)
                    with output.with_suffix('.log').open('w') as log:
                        completed = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                    invocations.append(dict(case=case, mode=mode, repetition=repetition,
                                            exit_code=completed.returncode, command=command, result=str(output.with_suffix('.json'))))
                    (directory / 'summary.json').write_text(json.dumps(invocations, indent=2) + '\n')
                    if completed.returncode:
                        raise RuntimeError(f'run failed; inspect {output.with_suffix(".log")}')
    summarize(directory, ROOT / args.output)


if __name__ == '__main__':
    main()
