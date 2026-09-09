#!/usr/bin/env python3
"""Preserve full experiment outcomes and independently recompute trace timings."""
import argparse
import collections
import csv
import hashlib
import json
import math
import pathlib
import statistics

from benchmark_analysis import caller_timings, distribution

ROOT = pathlib.Path(__file__).resolve().parents[1]
METRICS = ('vt_submit_to_callback_ns', 'public_complete_au_to_output_ns', 'preparation_ns',
           'post_parser_to_vt_submit_ns', 'submission_call_ns', 'callback_to_client_handoff_ns',
           'queue_wait_ns', 'scheduler_lateness_ns')
CONTROLS = dict([('qos-initiated', 'qos-default'), ('qos-interactive', 'qos-default'),
                 ('dispatch-sync', 'dispatch-async'), ('pacing-250', 'pacing-sleep'),
                 ('pacing-1000', 'pacing-sleep'), ('hevc-scan', 'baseline'),
                 ('parser-state', 'baseline'), ('pool-3', 'pool-0'), ('pool-6', 'pool-0'),
                 ('direct-1', 'direct-0'),
                 ('columns0', 'columns1'), ('columns2', 'columns1')])


def read_result(path, invocation):
    """Keep invalid attempts visible without treating their accounting as known."""
    if 'result_error' in invocation:
        return dict(status='MISSING_OR_INVALID_RESULT', reason=str(invocation['result_error']),
                    accounting_available=False)
    try:
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
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        return dict(status='MISSING_OR_INVALID_RESULT', reason=f'{type(error).__name__}: {error}',
                    accounting_available=False)


def enrich(path, result, fixture):
    manifest_path = pathlib.Path(fixture['manifest'])
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != fixture['manifest_sha256']:
        raise ValueError(f'manifest changed after run: {manifest_path}')
    manifest = json.loads(manifest_bytes)
    if result.get('fixture_sha256') != manifest['payload_sha256']:
        raise ValueError(f'result/fixture hash mismatch: {path}')
    result.update(caller_timings(path.with_suffix('.csv'), result))
    if not path.with_suffix('.csv').is_file():
        return dict(trace_available=False)
    with path.with_suffix('.csv').open(newline='') as source:
        rows = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(source)]
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
    assert vt['count'] == result['vt_submit_to_callback_ns']['count']
    if vt['count']:
        for key in ('median', 'p95', 'p99'):
            assert abs(vt[key] - result['vt_submit_to_callback_ns'][key]) < 1, (path, key)
    units = manifest['access_units']
    assert [u['frame_id'] for u in units] == list(range(len(units)))
    pictures = {}
    for kind, random_access in [('random_access', True), ('inter', False)]:
        selected = [r for r in steady if units[r['frame_id'] % len(units)]['random_access'] == random_access]
        pictures[kind] = dict(
            vt_submit_to_callback_ns=distribution([r['callback_ns']-r['vt_submit_ns'] for r in selected]),
            preparation_ns=distribution([r['preparation_end_ns']-r['preparation_start_ns']
                                         for r in selected if r['trace_valid'] & 1]),
            compressed_bytes=distribution([units[r['frame_id'] % len(units)]['length'] for r in selected]))
    returns = [r for r in steady if r['trace_valid'] & 4 and r['vt_return_ns'] >= r['vt_submit_ns']]
    after = [r for r in returns if r['callback_ns'] >= r['vt_return_ns']]
    return dict(trace_available=True, trace_rows=len(rows), steady_rows=len(steady), by_picture=pictures,
                vt_call_ns=distribution([r['vt_return_ns']-r['vt_submit_ns'] for r in returns]),
                vt_return_to_callback_ns=distribution([r['callback_ns']-r['vt_return_ns'] for r in after]),
                callback_before_return_rows=len(returns)-len(after), missing_return_rows=len(steady)-len(returns),
                raw_csv_sha256=hashlib.sha256(path.with_suffix('.csv').read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', nargs='+', required=True)
    parser.add_argument('--output', default='docs/evidence/experiment-comparison.json')
    args = parser.parse_args()
    runs, collections_metadata = [], {}
    seen_paths = set()
    for name in args.input:
        directory = ROOT / name
        summary = json.loads((directory / 'summary.json').read_text())
        tag = directory.name
        if tag in collections_metadata or directory.resolve() in seen_paths:
            raise ValueError(f'duplicate collection name or path would merge cohorts: {directory}')
        seen_paths.add(directory.resolve())
        collections_metadata[tag] = {k: v for k, v in summary.items() if k != 'runs'}
        seen = set()
        for invocation in summary['runs']:
            identity = (invocation['case'], invocation['setting'], invocation['repetition'])
            if identity in seen:
                raise ValueError(f'duplicate run identity: {tag} {identity}')
            seen.add(identity)
            path = pathlib.Path(invocation['result_file'])
            result = read_result(path, invocation)
            fixture = summary['fixtures'][invocation.get('fixture_id', invocation['case'])]
            phases = enrich(path, result, fixture) if result.get('fixture_sha256') else dict(trace_available=False)
            record = dict(invocation, collection=tag, result=result, phases=phases)
            cold_path = path.with_suffix('.cold.jsonl')
            if cold_path.is_file():
                record['cold_sessions'] = [json.loads(line) for line in cold_path.read_text().splitlines() if line]
            runs.append(record)
    groups = collections.defaultdict(list)
    for run in runs:
        groups[(run['collection'], run['case'], run['setting'])].append(run)
    aggregates = []
    for (collection, case, setting), group in groups.items():
        metrics = {}
        for metric in METRICS:
            values = [r['result'][metric] for r in group if r['result'].get(metric) and r['result'][metric].get('count')]
            if values:
                metrics[metric] = {key: statistics.median(v[key] for v in values) for key in ('median', 'p95', 'p99', 'mean')}
                metrics[metric]['per_run_medians'] = [v['median'] for v in values]
        result = dict(collection=collection, case=case, setting=setting, runs=len(group),
                      pass_runs=sum(r['exit_code'] == 0 and r['result'].get('status') == 'PASS' for r in group),
                      unknown_accounting_runs=sum('offered' not in r['result'] or 'displayed_outputs' not in r['result'] for r in group),
                      offered=sum(r['result']['offered'] for r in group) if all('offered' in r['result'] for r in group) else None,
                      displayed=sum(r['result']['displayed_outputs'] for r in group) if all('displayed_outputs' in r['result'] for r in group) else None,
                      known_offered=sum(r['result'].get('offered', 0) for r in group),
                      known_displayed=sum(r['result'].get('displayed_outputs', 0) for r in group), metrics=metrics)
        control = CONTROLS.get(setting)
        if control and (collection, case, control) in groups:
            controls = {r['repetition']: r for r in groups[(collection, case, control)]}
            passing_pairs = [(r, controls[r['repetition']]) for r in group if r['repetition'] in controls
                             and r['exit_code'] == 0 and r['result'].get('status') == 'PASS'
                             and controls[r['repetition']]['exit_code'] == 0
                             and controls[r['repetition']]['result'].get('status') == 'PASS']
            changes = {}
            for metric in METRICS:
                differences, percentages = [], []
                for run, baseline in passing_pairs:
                    candidate_value = (run['result'].get(metric) or {}).get('median')
                    baseline_value = (baseline['result'].get(metric) or {}).get('median')
                    if candidate_value is not None and baseline_value:
                        differences.append(candidate_value-baseline_value)
                        percentages.append(100*(candidate_value/baseline_value-1))
                if differences:
                    changes[metric] = dict(paired_median_delta_ns=statistics.median(differences),
                                           paired_median_change_percent=statistics.median(percentages),
                                           per_repetition_delta_ns=differences)
            result.update(control=control, qualified_passing_pairs=len(passing_pairs), paired_changes=changes)
        aggregates.append(result)
    document = dict(schema_version=1, collections=collections_metadata, runs=runs, aggregates=aggregates,
                    interpretation='All original outcomes retained. Aggregates are medians of per-run percentiles; '
                                   'paired changes compare only pairs of passing same-numbered repetitions within each collection. '
                                   'Other per-run and aggregate survivor timings remain diagnostic; failed outcomes and unknown accounting stay visible. '
                                   'Cold/warmup excluded only from steady distributions. No pooled timing across experiments. '
                                   'VT callback entry is not an isolated hardware timer. Phase percentiles are not additive. '
                                   'Synchronous return traces may be enriched after the run, as explicitly marked in result and raw CSV.')
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(document, indent=2).replace(str(ROOT.parent / 'moonlight-qt'), '$MOONLIGHT_QT_DIR').replace(str(ROOT), '$REPO')
    output.write_text(encoded + '\n')
    print(f'Preserved {len(runs)} runs and {len(aggregates)} aggregates: {output}')


if __name__ == '__main__':
    main()
