#!/usr/bin/env python3
"""Join VT signposts to replay CSV and partition trace-native call intervals.

Inputs for each --prefix: .json, .csv, -toc.xml, -region-of-interest.xml,
and -thread-state.xml. --output contains only aggregate diagnostics and hashes;
--local-output optionally preserves frame/thread identities in ignored results.
No profiler or decoder is executed. Existing outputs are never overwritten.
"""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import xml.etree.ElementTree as ET

from benchmark_analysis import distribution

SUBSYSTEM = 'net.edrisil.moonlight-apple-decoder'


class XMLTable:
    """xctrace exports reference values and nested thread/process identities by ID."""
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.ids = {e.get('id'): e for e in self.root.iter() if e.get('id')}

    def resolve(self, element):
        seen = set()
        while element is not None and element.get('ref'):
            ref = element.get('ref')
            if ref in seen or ref not in self.ids:
                raise ValueError(f'invalid XML reference: {ref}')
            seen.add(ref)
            element = self.ids[ref]
        return element

    def text(self, element):
        element = self.resolve(element)
        return (element.text or element.get('fmt', '')).strip() if element is not None else ''

    def integer(self, element):
        value = self.text(element).replace(',', '')
        if not re.fullmatch(r'-?(?:0x[0-9a-fA-F]+|[0-9]+)', value):
            raise ValueError(f'invalid integer XML value: {value!r}')
        return int(value, 16 if '0x' in value else 10)

    def child_integer(self, element, tag):
        element = self.resolve(element)
        child = element.find(tag) if element is not None else None
        return self.integer(child) if child is not None else None

    def metadata(self, element):
        element = self.resolve(element)
        if element is None or element.tag == 'sentinel':
            return {}
        # Structured narrative + integer nodes preserve full uint64 precision.
        text = ' '.join(self.text(child) for child in element) if len(element) else element.get('fmt', '')
        fields = {}
        for key, value in re.findall(r'(\w+)\s*=\s*(-?(?:0x[0-9a-fA-F]+|[\d,]+))', text):
            if key in fields:
                raise ValueError(f'duplicate signpost payload key: {key}')
            value = value.replace(',', '')
            fields[key] = int(value, 16 if '0x' in value else 10)
        return fields

    def rows(self, schema_name):
        for node in self.root.findall('.//node'):
            schema = node.find('schema')
            if schema is None or schema.get('name') != schema_name:
                continue
            columns = [c.findtext('mnemonic') for c in schema]
            for row in node.findall('row'):
                if len(row) != len(columns):
                    raise ValueError('XML row does not match schema column count')
                yield {key: self.resolve(value) for key, value in zip(columns, row)}


def overlap_states(start, end, intervals):
    """Partition union coverage, preserving holes and contradictory/duplicate rows."""
    if end < start:
        raise ValueError('negative signpost interval')
    changes = collections.defaultdict(list)
    changes[start]
    changes[end]
    for a, b, state in intervals:
        a, b = max(a, start), min(b, end)
        if a < b:
            changes[a].append((state, 1))
            changes[b].append((state, -1))
    active, totals = collections.Counter(), collections.Counter()
    previous = start
    for time in sorted(changes):
        duration = time-previous
        count = sum(active.values())
        if count == 0:
            totals['uncovered'] += duration
        elif count > 1:
            totals['ambiguous'] += duration
        else:
            totals[next(state for state, count in active.items() if count)] += duration
        for state, change in changes[time]:
            active[state] += change
            if active[state] < 0:
                raise ValueError('invalid interval sweep')
        previous = time
    return dict(totals)


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize_frames(frames):
    metrics = {}
    for key in ('raw_call_ns', 'raw_vt_ns', 'trace_call_ns', 'trace_frame_ns',
                'call_duration_delta_ns', 'frame_duration_delta_ns'):
        metrics[key] = distribution([f[key] for f in frames if f.get(key) is not None])
    names = {'Running', 'Runnable', 'Blocked', 'uncovered', 'ambiguous'}
    names.update(state for f in frames for state in f['submit_thread_states_ns'])
    states = {}
    for state in sorted(names):
        values = [f['submit_thread_states_ns'].get(state, 0) for f in frames]
        states[state] = dict(distribution(values), sum=sum(values), nonzero_frames=sum(v > 0 for v in values))
    return dict(frames=len(frames), metrics=metrics, submit_thread_states_ns=states,
        fully_covered_frames=sum(not f['submit_thread_states_ns'].get('uncovered', 0)
                                 and not f['submit_thread_states_ns'].get('ambiguous', 0) for f in frames),
        fully_known_frames=sum(not any(f['submit_thread_states_ns'].get(k, 0)
                                      for k in ('uncovered', 'ambiguous', 'Unknown')) for f in frames))


def analyze(prefix):
    paths = {name: pathlib.Path(str(prefix)+suffix) for name, suffix in (
        ('result', '.json'), ('csv', '.csv'), ('toc', '-toc.xml'),
        ('regions', '-region-of-interest.xml'), ('thread_states', '-thread-state.xml'))}
    result = json.loads(paths['result'].read_text())
    with paths['csv'].open(newline='') as source:
        rows = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(source)]
    toc = ET.parse(paths['toc']).getroot()
    target = toc.find('.//target/process')
    table = XMLTable(paths['regions'])
    candidates = []
    csv_submits = {row['vt_submit_ns'] for row in rows}
    matching_pids = set()
    for row in table.rows('region-of-interest'):
        name = table.text(row['name'])
        if name not in ('VTDecodeCall', 'VTFrame') or table.text(row['subsystem']) != SUBSYSTEM:
            continue
        begin, end = table.metadata(row['start-message']), table.metadata(row['end-message'])
        row_pid = table.child_integer(row['process'], 'pid')
        candidates.append((row, name, begin, end, row_pid))
        if begin.get('submit_ns') in csv_submits and row_pid is not None:
            matching_pids.add(row_pid)
    if len(matching_pids) != 1:
        raise ValueError(f'expected one process with exact CSV submit anchors; found {len(matching_pids)}')
    pid = next(iter(matching_pids))
    if target is not None and target.get('pid') and int(target.get('pid')) != pid:
        raise ValueError('TOC target PID differs from exact signpost/CSV anchor PID')
    regions = {'VTDecodeCall': {}, 'VTFrame': {}}
    errors, unmatched_regions = [], []
    for row, name, begin, end, row_pid in candidates:
        if row_pid != pid:
            continue
        submit = begin.get('submit_ns')
        if submit is None or 'work' not in begin or 'work' not in end:
            unmatched_regions.append(dict(name=name, reason='missing payload anchors'))
            continue
        if submit in regions[name]:
            errors.append(f'duplicate {name} submit timestamp')
            continue
        regions[name][submit] = dict(start=table.integer(row['start']), duration=table.integer(row['duration']),
            begin=begin, end=end, start_tid=table.child_integer(row['start-thread'], 'tid'),
            end_tid=table.child_integer(row['end-thread'], 'tid'))
    state_table = XMLTable(paths['thread_states'])
    states = collections.defaultdict(list)
    for row in state_table.rows('thread-state'):
        if state_table.child_integer(row['process'], 'pid') != pid:
            continue
        tid = state_table.child_integer(row['thread'], 'tid')
        if tid is None:
            continue
        start, duration = state_table.integer(row['start']), state_table.integer(row['duration'])
        if duration < 0:
            errors.append('negative thread-state duration')
            continue
        states[tid].append((start, start+duration, state_table.text(row['state'])))
    ids, submits = set(), set()
    first = {}
    for row in rows:
        if row['frame_id'] in ids or row['vt_submit_ns'] in submits:
            errors.append('duplicate CSV frame ID or submit timestamp')
        ids.add(row['frame_id'])
        submits.add(row['vt_submit_ns'])
        if row['status'] == 0 and row['displayed_outputs'] == 1:
            first[row['generation']] = min(first.get(row['generation'], row['frame_id']), row['frame_id'])
    accounting_errors = []
    process_exit = target.get('return-exit-status') if target is not None else None
    if result.get('status') != 'PASS' or result.get('hardware_validated') != 1 or process_exit not in (None, '0'):
        accounting_errors.append('replay, hardware validation, or process exit failed')
    if any(result.get(k) != len(rows) for k in ('offered', 'submitted', 'completed', 'displayed_outputs', 'internal_samples')):
        accounting_errors.append('replay totals disagree with CSV row count')
    if any(result.get(k) != 0 for k in ('rejected', 'failed_or_cancelled_or_dropped', 'scheduler_drops', 'resets',
                                       'trace_overflow', 'expected_display_mismatches', 'no_display', 'show_existing')):
        accounting_errors.append('loss, reset, or invalid trace/output accounting')
    frames, joins_failed = [], []
    for row in rows:
        submit = row['vt_submit_ns']
        call, frame = regions['VTDecodeCall'].get(submit), regions['VTFrame'].get(submit)
        problems = []
        if call is None or frame is None:
            joins_failed.append(dict(frame_id=row['frame_id'], reason='missing call/frame region'))
            continue
        if row['trace_valid'] & 10 != 10 or row['callback_ns'] < submit:
            problems.append('missing or invalid raw submit/callback')
        for interval in (call, frame):
            if interval['begin']['work'] != interval['end']['work'] or interval['duration'] < 0:
                problems.append('work identity or interval duration mismatch')
            if interval['end'].get('status') != 0:
                problems.append('unsuccessful signpost status')
        if call['begin']['work'] != frame['begin']['work'] or call['start_tid'] != frame['start_tid']:
            problems.append('call/frame identity mismatch')
        if frame['end'].get('callback_observed') != 1 or frame['end'].get('callback_ns') != row['callback_ns']:
            problems.append('callback payload mismatch')
        raw_return = call['end'].get('return_ns')
        if raw_return is None or raw_return < submit:
            problems.append('missing or invalid return payload')
        if row['trace_valid'] & 4 and raw_return != row['vt_return_ns']:
            problems.append('return payload mismatch')
        if problems:
            joins_failed.append(dict(frame_id=row['frame_id'], reasons=problems))
            continue
        a, b = call['start'], call['start']+call['duration']
        overlaps = overlap_states(a, b, states.get(call['start_tid'], []))
        frames.append(dict(frame_id=row['frame_id'], generation=row['generation'],
            steady=row['status'] == 0 and row['displayed_outputs'] == 1 and row['internal_samples'] == 1
                and not row['show_existing'] and row['frame_id'] >= result['warmup_frames']
                and row['frame_id'] != first.get(row['generation']),
            submit_tid=call['start_tid'], callback_tid=frame['end_tid'],
            submit_ns=submit, return_ns=raw_return, callback_ns=row['callback_ns'],
            csv_return_present=bool(row['trace_valid'] & 4),
            callback_before_return=row['callback_ns'] < raw_return,
            trace_call_start_ns=a, trace_call_end_ns=b, trace_frame_start_ns=frame['start'],
            trace_frame_end_ns=frame['start']+frame['duration'],
            raw_call_ns=raw_return-submit, raw_vt_ns=row['callback_ns']-submit,
            trace_call_ns=call['duration'], trace_frame_ns=frame['duration'],
            call_duration_delta_ns=call['duration']-(raw_return-submit),
            frame_duration_delta_ns=frame['duration']-(row['callback_ns']-submit),
            submit_thread_states_ns=overlaps))
    steady = [frame for frame in frames if frame['steady']]
    if not steady:
        errors.append('no joined steady frames')
    if unmatched_regions or joins_failed:
        errors.append('unmatched signposts or CSV frames')
    extra_regions = {name: len(set(values)-submits) for name, values in regions.items()}
    if any(extra_regions.values()):
        errors.append('signpost regions without corresponding CSV rows')
    summary_node = toc.find('.//summary')
    capture = {name: summary_node.findtext(name) for name in ('duration', 'recording-mode', 'end-reason', 'template-name')}
    aggregate = dict(case=prefix.name, sources={name: dict(name=path.name, sha256=file_hash(path)) for name, path in paths.items()},
        capture=dict(capture, process_exit_status=process_exit,
                     process_identity='Exact submit timestamp matches between signpost payloads and CSV'),
        replay={k: result.get(k) for k in ('status', 'codec', 'width', 'height', 'bit_depth', 'mode',
            'offered', 'submitted', 'completed', 'displayed_outputs', 'warmup_frames', 'fixture_sha256')},
        accounting_errors=accounting_errors, join_errors=errors, exact_joins=len(frames),
        csv_rows=len(rows), region_counts={k: len(v) for k, v in regions.items()}, extra_regions=extra_regions,
        unmatched_regions=len(unmatched_regions), unjoined_csv_rows=len(joins_failed),
        target_threads_with_state_records=len(states),
        submit_threads=len({f['submit_tid'] for f in frames}),
        submit_threads_without_state_records=sum(not states.get(tid) for tid in {f['submit_tid'] for f in frames}),
        callback_before_return_frames=sum(f['callback_before_return'] for f in frames),
        csv_missing_return_frames=sum(not f['csv_return_present'] for f in frames),
        all_frames=summarize_frames(frames), steady=summarize_frames(steady))
    aggregate['join_qualified'] = not accounting_errors and not errors and len(frames) == len(rows)
    aggregate['scheduling_qualified'] = aggregate['join_qualified'] and aggregate['steady']['fully_known_frames'] == len(steady)
    local = dict(case=prefix.name, target_pid=pid, frames=frames, unjoined=joins_failed,
                 unmatched_regions=unmatched_regions, target_thread_ids=sorted(states))
    return aggregate, local


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', nargs='+', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--local-output', type=pathlib.Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.local_output and args.local_output.exists():
        parser.error('output exists; preserve previous evidence with a new path')
    portable, local = [], []
    for prefix in args.prefix:
        aggregate, frames = analyze(prefix)
        portable.append(aggregate)
        local.append(frames)
        print(f"{prefix.name}: {aggregate['exact_joins']}/{aggregate['csv_rows']} exact joins; "
              f"{aggregate['steady']['fully_covered_frames']}/{aggregate['steady']['frames']} steady calls with full thread-state coverage")
    document = dict(schema_version=1, kind='per-frame-vt-system-trace-diagnostic', runs=portable,
        interpretation='All durations are nanoseconds. Submit-thread states overlap trace-native VTDecodeCall intervals, '
        'not inferred clock offsets. Raw payload timestamps must join CSV exactly. Unknown/Idle/Interrupted/Preempted '
        'stay separate; uncovered and ambiguous intervals are explicit. No hardware-only timing or uninstrumented '
        'performance claim. Signpost and raw timer durations differ by instrumentation boundaries.')
    with args.output.open('x') as out:
        json.dump(document, out, indent=2, allow_nan=False)
        out.write('\n')
    if args.local_output:
        with args.local_output.open('x') as out:
            json.dump(dict(runs=local), out, indent=2, allow_nan=False)
            out.write('\n')
    return int(any(not r['join_qualified'] for r in portable))


if __name__ == '__main__':
    raise SystemExit(main())
