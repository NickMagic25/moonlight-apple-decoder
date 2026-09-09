#!/usr/bin/env python3
"""Explain VT wait stages using an existing all-process trace, without replaying it.

The joined input comes from analyze-vt-profile.py --local-output. Syscalls are
streamed because an all-process export can be hundreds of MB. Only replay and
one decoder-service candidate's relevant rows are retained in the final output.
Stage matches use exact replay frame windows; service ordering alone does not
prove a message dependency. Same-condition-object signals and scheduler waker
edges provide stronger, separate evidence.
"""
import argparse
import bisect
import collections
import hashlib
import json
import pathlib
import xml.etree.ElementTree as ET


class HashingReader:
    def __init__(self, source):
        self.source, self.hash = source, hashlib.sha256()

    def read(self, size=-1):
        data = self.source.read(size)
        self.hash.update(data)
        return data


class StreamValues:
    """Resolve preceding xctrace value IDs without keeping the complete XML DOM."""
    keep = {'start-time', 'duration', 'duration-on-core', 'duration-waiting',
            'syscall-arg', 'syscall-return', 'syscall', 'pid', 'tid', 'process',
            'thread', 'tagged-backtrace', 'backtrace', 'frame', 'binary'}

    def __init__(self, symbol_aliases=None):
        self.ids = {}
        self.symbol_aliases = symbol_aliases or {}

    def value(self, element):
        if element.get('ref'):
            ref = element.get('ref')
            if ref not in self.ids and element.tag in self.keep:
                raise ValueError(f'unresolved {element.tag} XML reference {ref}')
            return self.ids.get(ref)
        if element.tag not in self.keep:
            return None
        children = [self.value(c) for c in element]
        tag = element.tag
        if tag == 'process':
            result = {'pid': children[0], 'name': element.get('fmt', '')}
        elif tag == 'thread':
            result = {'tid': children[0], 'owner': children[1]}
        elif tag == 'frame':
            result = element.get('name') or ('@'+element.get('addr') if element.get('addr') else '?')
            result = self.symbol_aliases.get(result, result)
        elif tag == 'binary':
            result = None
        elif tag == 'backtrace':
            result = tuple(children)
        elif tag == 'tagged-backtrace':
            result = children[0] if children else ()
        elif tag == 'syscall':
            result = (element.text or '').strip()
        else:
            text = (element.text or '').strip()
            result = int(text, 16 if text.lower().startswith('0x') else 10) if text else None
        if element.get('id'):
            self.ids[element.get('id')] = result
        return result


def distribution(values):
    values = sorted(values)
    if not values:
        return {'count': 0}
    def percentile(p):
        index = (len(values)-1)*p
        lo = int(index)
        hi = min(lo+1, len(values)-1)
        return values[lo] + (values[hi]-values[lo])*(index-lo)
    return {'count': len(values), 'p50_ns': percentile(.5), 'p95_ns': percentile(.95),
            'p99_ns': percentile(.99), 'sum_ns': sum(values)}


def has_sync_xpc(stack):
    return 'xpc_connection_send_message_with_reply_sync' in stack


def service_category(stack):
    if 'IOConnectCallMethod' in stack:
        if 'IODispatchCalloutFromCFMessage' in stack:
            return 'output_io'
        if '_dispatch_call_block_and_release' in stack:
            return 'decode_io'
    if 'xpc_connection_send_message' in stack:
        if '_xpc_connection_call_event_handler' in stack:
            return 'immediate_reply'
        if '_dispatch_call_block_and_release' in stack:
            return 'decode_ack'
    if has_sync_xpc(stack):
        return 'output_rpc_syscall'
    return None


def target_category(call, stack):
    if call == 'BSC_psynch_cvwait':
        return 'condition_wait'
    if call == 'BSC_psynch_cvsignal':
        return 'condition_signal'
    if has_sync_xpc(stack):
        return 'submit_rpc_syscall'
    if 'IOSurfaceClientLookupFromMachPort' in stack:
        return 'surface_lookup'
    return None


def stream_syscalls(path, target_pid, window_start, window_end, symbol_aliases=None):
    resolver = StreamValues(symbol_aliases)
    rows, candidates, names = [], collections.defaultdict(list), {}
    parsed = 0
    columns = None
    root = None
    with path.open('rb') as raw:
        reader = HashingReader(raw)
        for event, element in ET.iterparse(reader, events=('start', 'end')):
            if root is None:
                root = element
            if event != 'end':
                continue
            if element.tag == 'schema':
                if element.get('name') != 'syscall':
                    raise ValueError('expected a syscall table export')
                columns = [c.findtext('mnemonic') for c in element.findall('col')]
            if element.tag != 'row':
                continue
            if columns is None or len(columns) != len(element):
                raise ValueError('syscall schema/row column mismatch')
            v = dict(zip(columns, (resolver.value(c) for c in element)))
            parsed += 1
            process, thread = v.get('process'), v.get('thread')
            start, duration = v.get('start'), v.get('duration')
            if process and thread and start is not None and duration is not None:
                pid = process['pid']
                names[pid] = process['name']
                end = start + duration
                if end >= window_start and start <= window_end:
                    stack = v.get('backtrace') or ()
                    category = (target_category(v.get('call'), stack) if pid == target_pid
                                else service_category(stack))
                    if not category and pid != target_pid and 'VTDecoder' in process['name']:
                        category = 'unclassified_service_syscall'
                    if category:
                        row = {'pid': pid, 'tid': thread['tid'], 'start_ns': start,
                               'end_ns': end, 'duration_ns': duration, 'call': v.get('call'),
                               'args': [v.get(f'arg{i}') for i in range(1, 5)],
                               'result': v.get('return'), 'stack': stack, 'category': category}
                        (rows if pid == target_pid else candidates[pid]).append(row)
            element.clear()
            root.clear()
        digest = reader.hash.hexdigest()
    return rows, candidates, names, {'parsed_rows': parsed, 'sha256': digest}


def select_service(candidates, names, requested_pid=None):
    required = {'immediate_reply', 'decode_ack', 'decode_io', 'output_io', 'output_rpc_syscall'}
    eligible = [pid for pid, rows in candidates.items()
                if required <= {r['category'] for r in rows}]
    if requested_pid is not None:
        if requested_pid not in candidates:
            raise ValueError('requested service PID has no retained syscall evidence')
        return requested_pid, 'caller-specified PID from independent process metadata; missing stack matches remain explicit'
    named = [pid for pid in candidates if 'VTDecoder' in names.get(pid, '')]
    if len(named) == 1:
        return named[0], 'VTDecoder process name in trace metadata; missing stack matches remain explicit'
    if len(eligible) != 1:
        raise ValueError(f'expected one decoder-service candidate; found {len(eligible)}; supply --service-pid from independent metadata')
    return eligible[0], 'unique process with XPC reply, decode IOKit and output IOKit stack patterns; name unconfirmed'


def classify_rpc_pair(rows):
    """A send trap plus receive trap can implement ONE synchronous XPC RPC."""
    rows = sorted(rows, key=lambda r: r['start_ns'])
    if len(rows) != 2 or not all(has_sync_xpc(r['stack']) for r in rows):
        return None
    send = [r for r in rows if '_dispatch_mach_msg_send' in r['stack']]
    receive = [r for r in rows if 'mach_msg_overwrite' in r['stack'] and
               '_dispatch_mach_msg_send' not in r['stack']]
    if len(send) != 1 or len(receive) != 1 or send[0]['end_ns'] > receive[0]['start_ns']:
        return None
    # The pair is a stack/ordering interpretation, not a transaction-ID match.
    return {'send': send[0], 'receive': receive[0], 'logical_rpc_count': 1}


def matching_condition_signals(wait, signals):
    address = wait.get('args', [None])[0]
    if address is None:
        return []
    return [r for r in signals if r.get('args', [None])[0] == address and
            wait['start_ns'] <= r['start_ns'] <= wait['end_ns']]


def qualify_joined_subset(run, aggregate):
    """Accept capture-boundary omissions, never interior gaps or bad payloads."""
    frames = run['frames']
    ids = [f['frame_id'] for f in frames]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('empty or duplicate exact joined frames')
    if aggregate.get('accounting_errors'):
        raise ValueError('replay accounting failed')
    if aggregate.get('exact_joins') != len(frames):
        raise ValueError('join summary/local exact-frame counts disagree')
    if any(aggregate.get('extra_regions', {}).values()) or run.get('unmatched_regions'):
        raise ValueError('unmatched or extra signpost regions require investigation')
    if any(e != 'unmatched signposts or CSV frames' for e in aggregate.get('join_errors', [])):
        raise ValueError('join summary contains a non-boundary error')
    first, last = min(ids), max(ids)
    unjoined = run.get('unjoined', [])
    if set(ids) != set(range(first, last+1)):
        raise ValueError('interior gap in exact joined frame sequence')
    if len({entry['frame_id'] for entry in unjoined}) != len(unjoined):
        raise ValueError('duplicate omitted frame identities')
    for entry in unjoined:
        if entry.get('reason') != 'missing call/frame region' or entry.get('reasons'):
            raise ValueError('unjoined frame has a payload/identity mismatch')
        if first <= entry['frame_id'] <= last:
            raise ValueError('interior gap in exact joined frame sequence')
    if aggregate.get('csv_rows') != len(frames)+len(unjoined):
        raise ValueError('exact and omitted frame counts do not cover CSV rows')
    return {'full_run_join_qualified': bool(aggregate.get('join_qualified')),
            'exact_subset_qualified': True, 'partial_capture': bool(unjoined),
            'csv_rows': aggregate['csv_rows'], 'exact_joined_frames': len(frames),
            'omitted_boundary_frames': len(unjoined),
            'first_joined_frame_id': first, 'last_joined_frame_id': last}


def analyze_frames(frames, rows, target_pid, service_pid):
    rows = sorted(rows, key=lambda r: r['start_ns'])
    starts = [r['start_ns'] for r in rows]
    result, metrics, matches = [], collections.defaultdict(list), collections.Counter()
    for frame in frames:
        a, b, c = (frame[k] for k in ('trace_call_start_ns', 'trace_call_end_ns', 'trace_frame_end_ns'))
        window = rows[bisect.bisect_left(starts, a):bisect.bisect_right(starts, c)]
        submit = [r for r in window if r['pid'] == target_pid and r['tid'] == frame['submit_tid'] and r['end_ns'] <= b]
        groups = collections.defaultdict(list)
        for r in window:
            if r['pid'] == service_pid:
                groups[r['category']].append(r)
        rpc = [r for r in submit if r['category'] == 'submit_rpc_syscall']
        waits = [r for r in submit if r['category'] == 'condition_wait']
        signals = [r for r in window if r['pid'] == target_pid and r['category'] == 'condition_signal']
        signal = matching_condition_signals(waits[0], signals) if len(waits) == 1 else []
        lookup = [r for r in window if r['pid'] == target_pid and r['tid'] == frame['callback_tid'] and r['category'] == 'surface_lookup']
        pair, output_pair = classify_rpc_pair(rpc), classify_rpc_pair(groups['output_rpc_syscall'])
        counts = {'submit_rpc_syscalls': len(rpc), 'submit_rpc_send_receive_pairs': int(pair is not None),
                  'condition_wait': len(waits), 'same_condition_signal': len(signal),
                  'client_surface_lookup': len(lookup), 'output_rpc_send_receive_pairs': int(output_pair is not None)}
        counts.update({k: len(groups[k]) for k in ('immediate_reply', 'decode_ack', 'decode_io', 'output_io', 'output_rpc_syscall')})
        for key, count in counts.items():
            matches[f'{key}:{count}'] += 1
        values = {'api_call': b-a, 'submit_to_callback': c-a, 'return_to_callback': c-b}
        anchors = {'call_start': a, 'call_end': b, 'callback_entry': c}
        if pair:
            send, receive = pair['send'], pair['receive']
            anchors.update(rpc_send_start=send['start_ns'], rpc_send_end=send['end_ns'],
                           rpc_receive_start=receive['start_ns'], rpc_receive_end=receive['end_ns'])
            values.update(submit_to_rpc=send['start_ns']-a,
                          rpc_send_through_receive_end=receive['end_ns']-send['start_ns'])
        if len(waits) == 1:
            anchors.update(condition_wait_start=waits[0]['start_ns'], condition_wait_end=waits[0]['end_ns'])
            values['condition_wait'] = waits[0]['duration_ns']
        immediate_in_rpc = [r for r in groups['immediate_reply'] if pair and
                            pair['send']['start_ns'] <= r['start_ns'] and r['end_ns'] <= pair['receive']['end_ns']]
        counts['immediate_reply_inside_submit_rpc'] = len(immediate_in_rpc)
        matches[f'immediate_reply_inside_submit_rpc:{len(immediate_in_rpc)}'] += 1
        if len(immediate_in_rpc) == 1:
            r = immediate_in_rpc[0]
            anchors.update(service_immediate_reply_start=r['start_ns'], service_immediate_reply_end=r['end_ns'])
        if len(groups['decode_ack']) == 1:
            ack = groups['decode_ack'][0]
            anchors.update(service_decode_ack_start=ack['start_ns'], service_decode_ack_end=ack['end_ns'])
            if groups['decode_io']:
                anchors['service_decode_first_io'] = groups['decode_io'][0]['start_ns']
                values['service_first_decode_io_to_ack_end'] = ack['end_ns']-groups['decode_io'][0]['start_ns']
                values['service_decode_io_syscall_sum'] = sum(r['duration_ns'] for r in groups['decode_io'])
        if len(signal) == 1:
            anchors.update(local_condition_signal_start=signal[0]['start_ns'], local_condition_signal_end=signal[0]['end_ns'])
            values['local_signal_end_to_wait_end'] = waits[0]['end_ns']-signal[0]['end_ns']
            if len(groups['decode_ack']) == 1:
                values['service_ack_end_to_local_signal_start'] = signal[0]['start_ns']-groups['decode_ack'][0]['end_ns']
        if groups['output_io']:
            first = groups['output_io'][0]['start_ns']
            anchors['first_recorded_service_output_io'] = first
            values['return_to_first_recorded_service_output_io'] = first-b
            values['first_recorded_service_output_io_to_callback'] = c-first
        if output_pair:
            anchors.update(service_output_rpc_send_start=output_pair['send']['start_ns'],
                           service_output_rpc_receive_end=output_pair['receive']['end_ns'])
            values['service_output_send_to_callback'] = c-output_pair['send']['start_ns']
        if len(lookup) == 1:
            anchors.update(client_surface_lookup_start=lookup[0]['start_ns'], client_surface_lookup_end=lookup[0]['end_ns'])
            values['client_surface_lookup_syscall'] = lookup[0]['duration_ns']
            values['client_surface_lookup_start_to_callback'] = c-lookup[0]['start_ns']
        for key, value in values.items():
            metrics[key].append(value)
        result.append({'frame_id': frame['frame_id'], 'counts': counts, 'anchors_ns': anchors,
                       'metrics_ns': values, 'condition_waits': waits, 'condition_signals': signal,
                       'submit_rpc_syscalls': rpc, 'service_decode_io': groups['decode_io'],
                       'service_output_io': groups['output_io']})
    overlapping = sum(a['trace_frame_end_ns'] > b['trace_frame_start_ns'] for a, b in zip(frames, frames[1:]))
    return {'frames': len(frames), 'overlapping_adjacent_frame_windows': overlapping,
            'match_counts': dict(matches), 'metrics': {k: distribution(v) for k, v in metrics.items()}}, result


LIMITATIONS = [
    'Service events are temporally matched inside exact replay frame windows, not matched by transaction IDs. Extra/missing matches are counted, not silently forced.',
    'A synchronous XPC send trap and receive trap are one candidate RPC pair, not two independent RPCs. Stack classification and static code review support this interpretation.',
    'Same condition object addresses link local condition signals to submit waits; scheduler waker edges provide separate evidence.',
    'The first recorded service output IOKit call is not a hardware completion timestamp. The preceding gap includes an unknown combination of hardware, driver and scheduling time.',
    'Mach syscall arguments do not expose the IOConnectCallMethod selector or its structure payload. This analyzer does not name private driver methods.',
    'Service IOKit syscall sums are elapsed wall intervals, not CPU or hardware time. They overlap submit-thread waits and must not be added to those waits.',
    'Independent percentile values do not add to a percentile of total frame latency.',
    'Output RPC receive may finish after callback entry; only activity preceding callback entry belongs in submit-to-callback latency.',
    'This is an instrumented, paced trace; benchmark claims require separate uninstrumented replay measurements.',
]


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=pathlib.Path, required=True, help='trace export prefix')
    parser.add_argument('--joined', type=pathlib.Path, required=True, help='analyze-vt-profile.py local JSON')
    parser.add_argument('--join-summary', type=pathlib.Path, required=True, help='analyze-vt-profile.py portable JSON for accounting and partial-capture checks')
    parser.add_argument('--case', help='joined run name; defaults to prefix basename')
    parser.add_argument('--syscall', type=pathlib.Path, help='override PREFIX-syscall.xml')
    parser.add_argument('--thread-state', type=pathlib.Path, help='override PREFIX-thread-state.xml')
    parser.add_argument('--service-pid', type=int, help='service PID established independently, if inference is ambiguous')
    parser.add_argument('--stack-symbols', type=pathlib.Path, help='optional verified exact frame-text aliases JSON; no fuzzy address matching')
    parser.add_argument('--output', type=pathlib.Path, required=True, help='portable aggregate JSON')
    parser.add_argument('--local-output', type=pathlib.Path, help='optional frame/condition/thread identities; keep local')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    for path in (args.output, args.local_output):
        if path and path.exists() and not args.overwrite:
            parser.error(f'output already exists: {path}; choose another path or --overwrite')
    runs = json.loads(args.joined.read_text())['runs']
    matching = [r for r in runs if r['case'] == (args.case or args.prefix.name)]
    if len(matching) != 1:
        parser.error('expected exactly one matching joined run')
    run = matching[0]
    summaries = json.loads(args.join_summary.read_text())['runs']
    matching_summaries = [r for r in summaries if r['case'] == run['case']]
    if len(matching_summaries) != 1:
        parser.error('expected exactly one matching join summary')
    qualification = qualify_joined_subset(run, matching_summaries[0])
    frames = sorted((f for f in run['frames'] if f['steady']), key=lambda f: f['trace_call_start_ns'])
    if not frames:
        parser.error('joined run contains no steady frames')
    target_pid = run['target_pid']
    syscall = args.syscall or pathlib.Path(str(args.prefix)+'-syscall.xml')
    state = args.thread_state or pathlib.Path(str(args.prefix)+'-thread-state.xml')
    symbol_data = json.loads(args.stack_symbols.read_text()) if args.stack_symbols else None
    aliases = symbol_data.get('aliases', {}) if symbol_data else {}
    if not isinstance(aliases, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in aliases.items()):
        parser.error('stack symbols aliases must map exact frame text to symbol strings')
    target, candidates, names, parsed = stream_syscalls(syscall, target_pid,
        frames[0]['trace_call_start_ns'], max(f['trace_frame_end_ns'] for f in frames), aliases)
    service_pid, reason = select_service(candidates, names, args.service_pid)
    summary, details = analyze_frames(frames, target+candidates[service_pid], target_pid, service_pid)
    portable = {'schema_version': 1, 'case': run['case'], 'joined_frames': len(run['frames']),
                'qualification': qualification,
                'service_identification': {'method': reason, 'name_confirmed': 'VTDecoder' in names.get(service_pid, '')},
                'syscalls': summary, 'limitations': LIMITATIONS,
                'artifacts': {'joined': {'filename': args.joined.name, 'sha256': file_hash(args.joined)},
                              'join_summary': {'filename': args.join_summary.name, 'sha256': file_hash(args.join_summary)},
                              'analyzer': {'filename': pathlib.Path(__file__).name, 'sha256': file_hash(pathlib.Path(__file__))},
                              'syscall': {'filename': syscall.name, 'sha256': parsed['sha256'], 'parsed_rows': parsed['parsed_rows']}}}
    symbol_evidence = pathlib.Path('docs/evidence/vt-wait-symbols.json')
    if args.stack_symbols:
        portable['artifacts']['stack_symbols'] = {'filename': args.stack_symbols.name, 'sha256': file_hash(args.stack_symbols),
            'method': 'Exact exported frame-text aliases resolved against verified image UUIDs and shared-cache mapping; no fuzzy address matching.',
            'aliases': len(aliases)}
        portable['limitations'] = LIMITATIONS + ['Unnamed stack frames were restored using supplied exact aliases; that mapping must be verified against the recorded image UUIDs and addresses for this capture.']
    if symbol_evidence.exists():
        portable['related_static_evidence'] = {'path': str(symbol_evidence), 'sha256': file_hash(symbol_evidence),
            'scope': 'Supports the old capture RPC interpretation and emitted-frame metadata chain; does not establish per-frame transaction identities.'}
    local = {'case': run['case'], 'target_pid': target_pid, 'service_pid': service_pid,
             'service_name': names.get(service_pid), 'frames': details,
             'selected_service_syscalls': candidates[service_pid]}
    if state.exists():
        from vt_wait_states import analyze_state_dependencies
        state_summary, state_details = analyze_state_dependencies(state, frames, target_pid, service_pid, details)
        portable['thread_states'] = state_summary
        portable['artifacts']['thread_state'] = {'filename': state.name, 'sha256': file_hash(state)}
        helper_path = pathlib.Path(__file__).with_name('vt_wait_states.py')
        portable['artifacts']['state_analyzer'] = {'filename': helper_path.name, 'sha256': file_hash(helper_path)}
        local['thread_states'] = state_details
    else:
        portable['limitations'] = LIMITATIONS + ['No thread-state export supplied; scheduler waker corroboration is absent.']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(portable, indent=2)+'\n')
    if args.local_output:
        args.local_output.parent.mkdir(parents=True, exist_ok=True)
        args.local_output.write_text(json.dumps(local, indent=2)+'\n')
    print(json.dumps({'case': run['case'], 'frames': len(frames), 'output': str(args.output)}, indent=2))


if __name__ == '__main__':
    main()
