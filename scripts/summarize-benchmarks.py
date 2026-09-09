#!/usr/bin/env python3
"""Preserve measured results and portable provenance, without generated media."""
import argparse
import json
import pathlib
from benchmark_analysis import caller_timings

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='results/benchmarks')
    parser.add_argument('--output', default='docs/evidence/benchmarks.json')
    args = parser.parse_args()
    source = ROOT / args.input
    runs = []
    environments = {}
    for directory in sorted(p for p in source.iterdir() if p.is_dir()):
        summary_path = directory / 'summary.json'
        summary = json.loads(summary_path.read_text()) if summary_path.is_file() else {}
        environment = directory / 'environment.json'
        if environment.is_file():
            environments[directory.name] = json.loads(environment.read_text())
        for path in sorted(directory.glob('*rep*.json')):
            result = json.loads(path.read_text())
            if result.get('inflight'):
                result['scheduler_queue_depth'] = summary.get('native_scheduler_queue_depth', 16)
            else:
                result['scheduler_queue_policy'] = 'Drains scheduled AUs without age-based dropping'
            result.update(caller_timings(path.with_suffix('.csv'), result))
            seconds = result.get('run_seconds')
            if seconds:
                result.setdefault('decoded_fps', result.get('displayed_outputs', 0) / seconds)
                result.setdefault('admission_fps', result.get('submitted', 0) / seconds)
            runs.append(dict(preset=directory.name, file=str(path.relative_to(ROOT)), result=result))
    document = dict(schema_version=1, headless_only=True,
        comparison='Identical saved access units, fixed offered deadlines, hardware YUV output. '
                   'Native VT call to callback and FFmpeg send to receive are different intervals.',
        environments=environments, runs=runs)
    # Local raw artifacts keep exact invocation paths. The portable evidence
    # uses placeholders and fixture/binary hashes, never a developer home path.
    encoded = json.dumps(document, indent=2)
    encoded = encoded.replace(str(ROOT.parent / 'moonlight-qt'), '$MOONLIGHT_QT_DIR')
    encoded = encoded.replace(str(ROOT), '$REPO')
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(encoded + '\n')
    print(f'Preserved {len(runs)} measured runs in {output.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
