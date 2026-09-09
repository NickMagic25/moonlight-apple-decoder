"""Thread-state evidence for exact VT frame intervals; no live profiling.

This helper deliberately calls sleeping time ``Blocked`` rather than hardware
decode time. A Runnable note identifies the immediate kernel waker, not the
complete dependency chain or the owner of a user-space synchronization object.
"""
import collections
import importlib.util
import pathlib
import re

from benchmark_analysis import distribution

_SPEC = importlib.util.spec_from_file_location(
    '_vt_profile', pathlib.Path(__file__).with_name('analyze-vt-profile.py'))
_PROFILE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROFILE)


def read_target_states(path, target_pid, service_pid):
    table = _PROFILE.XMLTable(path)
    states = collections.defaultdict(list)
    selected_pids = {target_pid}
    if service_pid is not None:
        selected_pids.add(service_pid)

    def identity(element):
        element = table.resolve(element)
        if element is None or element.tag == 'sentinel':
            return None
        process = table.resolve(element.find('process'))
        return dict(tid=table.child_integer(element, 'tid'),
                    pid=table.child_integer(process, 'pid'), label=element.get('fmt', ''))

    for row in table.rows('thread-state'):
        pid = table.child_integer(row['process'], 'pid')
        if pid not in selected_pids:
            continue
        tid = table.child_integer(row['thread'], 'tid')
        if tid is None:
            continue
        start, duration = table.integer(row['start']), table.integer(row['duration'])
        if duration < 0:
            raise ValueError('negative thread-state duration')
        note = row.get('note')
        wakers = []
        if note is not None:
            for child in note:
                if table.resolve(child).tag == 'thread':
                    wakers.append(identity(child))
        states[tid].append(dict(start=start, end=start+duration, pid=pid,
            state=table.text(row['state']), note=note.get('fmt', '') if note is not None else '',
            wakers=[w for w in wakers if w is not None]))
    return {tid: sorted(rows, key=lambda r: (r['start'], r['end']))
            for tid, rows in states.items()}


def _overlapping(states, start, end):
    return [s for s in states if s['start'] < end and s['end'] > start]


def _partition(states, start, end):
    return _PROFILE.overlap_states(start, end,
        [(s['start'], s['end'], s['state']) for s in _overlapping(states, start, end)])


def _wake_edges(states, start, end):
    # Count a transition only if its timestamp is inside the interval. A
    # Runnable interval beginning earlier is coverage, not a second wake edge.
    return [s for s in states if s['state'] == 'Runnable' and start <= s['start'] < end]


def _aggregate(values):
    return dict(distribution(values), sum=sum(values))


def analyze_state_dependencies(thread_state_path, frames, target_pid, service_pid,
                               syscall_frames=None, *, states=None):
    """Return (portable aggregate, local details), excluding non-steady frames.

    ``syscall_frames`` optionally contains per-frame dictionaries with frame_id,
    condition_waits, condition_signals and submit_rpc_syscalls. Event fields are
    start_ns/end_ns/pid/tid/args. ``states`` supports focused synthetic tests or
    reuse of an already parsed export; its keys are numeric TIDs.
    """
    if states is None:
        states = read_target_states(thread_state_path, target_pid, service_pid)
    selected = [f for f in frames if f.get('steady', False)]
    if len({f['frame_id'] for f in selected}) != len(selected):
        raise ValueError('duplicate steady frame ID')
    submit_tids = {f['submit_tid'] for f in selected}
    callback_tids = {f['callback_tid'] for f in selected}

    def origin(waker):
        if waker['pid'] == 0 and re.match(r'^AppleAVD\s+\(', waker.get('label', '')):
            return 'kernel_AppleAVD'
        if waker['pid'] == target_pid:
            if waker['tid'] in submit_tids:
                return 'replay_submit_thread'
            if waker['tid'] in callback_tids:
                return 'replay_callback_thread'
            return 'replay_other_thread'
        if service_pid is not None and waker['pid'] == service_pid:
            return 'selected_service_process'
        return 'unresolved_process' if waker['pid'] is None else 'other_process'

    per_syscall = ({r['frame_id']: r for r in syscall_frames}
                   if syscall_frames is not None else {})
    details, invalid = [], []
    service_interval_selection = collections.Counter()
    role_wakers = collections.defaultdict(collections.Counter)
    for frame in selected:
        fid, stid, ctid = frame['frame_id'], frame['submit_tid'], frame['callback_tid']
        start, returned, callback = (frame['trace_call_start_ns'],
            frame['trace_call_end_ns'], frame['trace_frame_end_ns'])
        if returned < start or callback < returned or frame.get('callback_before_return', False):
            invalid.append(dict(frame_id=fid, reason='nonsequential call/return/callback'))
            continue
        record = dict(frame_id=fid, submit_tid=stid, callback_tid=ctid,
                      call_start=start, return_event=returned, callback_event=callback)
        for role, tid, a, b in [('submit_call', stid, start, returned),
                              ('submit_after_return', stid, returned, callback),
                              ('callback_after_return', ctid, returned, callback)]:
            rows = states.get(tid, [])
            edges = _wake_edges(rows, a, b)
            record[role] = dict(duration_ns=b-a, states_ns=_partition(rows, a, b),
                                runnable_edges=edges)
            for edge in edges:
                if edge['wakers']:
                    role_wakers[role].update(origin(w) for w in edge['wakers'])
                else:
                    role_wakers[role]['timer' if 'timer expiration' in edge['note']
                                      else 'no_thread_waker'] += 1

        callback_rows = states.get(ctid, [])
        at_callback = [s for s in callback_rows if s['start'] <= callback < s['end']]
        record['callback_event_state'] = (at_callback[0]['state'] if len(at_callback) == 1
            else 'uncovered' if not at_callback else 'ambiguous')
        wakes = [s for s in _wake_edges(callback_rows, returned, callback) if s['end'] <= callback]
        last = max(wakes, key=lambda s: s['start']) if wakes else None
        record['last_callback_runnable'] = last
        if last is not None:
            record['last_callback_runnable_ns'] = last['end']-last['start']
            record['after_last_runnable_until_callback_ns'] = callback-last['end']
            tail = _partition(callback_rows, last['end'], callback)
            record['last_runnable_followed_by_only_running'] = not any(
                value for state, value in tail.items() if state != 'Running')

        record['syscalls'] = []
        calls = per_syscall.get(fid, {})
        output_io = calls.get('service_output_io', [])
        output_tids = {s['tid'] for s in output_io if s.get('pid') == service_pid}
        if len(output_tids) == 1:
            output_tid = next(iter(output_tids))
            first_io = min(s['start_ns'] for s in output_io
                           if s.get('pid') == service_pid and s['tid'] == output_tid)
            if returned <= first_io <= callback:
                rows = states.get(output_tid, [])
                edges = _wake_edges(rows, returned, first_io)
                role = 'service_output_before_first_io'
                record[role] = dict(duration_ns=first_io-returned,
                    states_ns=_partition(rows, returned, first_io), runnable_edges=edges,
                    tid=output_tid, first_io_ns=first_io)
                for edge in edges:
                    role_wakers[role].update(origin(w) for w in edge['wakers'])
                if len(edges) == 1 and len(edges[0]['wakers']) == 1:
                    wake = edges[0]
                    record['service_output_notification'] = dict(
                        origin=origin(wake['wakers'][0]), waker=wake['wakers'][0],
                        return_to_wake_ns=wake['start']-returned,
                        runnable_ns=min(wake['end'], first_io)-wake['start'],
                        wake_to_first_io_ns=first_io-wake['start'])
                service_interval_selection['qualified'] += 1
            else:
                service_interval_selection['first_io_outside_after_return_window'] += 1
        else:
            service_interval_selection['missing_output_thread' if not output_tids
                                       else 'ambiguous_output_threads'] += 1
        for kind, key in [('condition_wait', 'condition_waits'), ('sync_xpc', 'submit_rpc_syscalls')]:
            for call in calls.get(key, []):
                a, b = call['start_ns'], call['end_ns']
                edges = _wake_edges(states.get(stid, []), a, b)
                item = dict(kind=kind, call=call, wake_edges=edges,
                            states_ns=_partition(states.get(stid, []), a, b))
                if kind == 'condition_wait':
                    args = call.get('args', [])
                    signals = [s for s in calls.get('condition_signals', [])
                        if args and args[0] is not None and s.get('args') and s['args'][0] == args[0]
                        and s['pid'] == call['pid'] and a <= s['start_ns'] <= s['end_ns'] <= b]
                    wakers = [w for e in edges for w in e['wakers']]
                    item['matching_signals'] = signals
                    item['unique_condition_signal'] = len(signals) == 1
                    item['signal_matches_unique_kernel_waker'] = (len(signals) == len(wakers) == 1
                        and signals[0]['pid'] == wakers[0]['pid']
                        and signals[0]['tid'] == wakers[0]['tid'])
                    item['wake_inside_signal'] = (len(signals) == len(edges) == 1 and
                        signals[0]['start_ns'] <= edges[0]['start'] <= signals[0]['end_ns'])
                record['syscalls'].append(item)
        details.append(record)

    summary = dict(steady_frames=len(selected), analyzed_frames=len(details),
        excluded_nonsequential_frames=len(invalid), roles={})
    for role in ('submit_call', 'submit_after_return', 'callback_after_return',
                 'service_output_before_first_io'):
        role_rows = [r for r in details if role in r]
        names = {'Running', 'Runnable', 'Blocked', 'uncovered', 'ambiguous'}
        names.update(k for row in role_rows for k in row[role]['states_ns'])
        summary['roles'][role] = dict(
            frames=len(role_rows),
            duration_ns=_aggregate([r[role]['duration_ns'] for r in role_rows]),
            states_ns={name: _aggregate([r[role]['states_ns'].get(name, 0) for r in role_rows])
                       for name in sorted(names)},
            fully_covered_frames=sum(not any(r[role]['states_ns'].get(k, 0)
                for k in ('uncovered', 'ambiguous')) for r in role_rows),
            wake_origins=dict(role_wakers[role]))
    summary['service_output_interval_selection'] = dict(service_interval_selection)
    notifications = [r['service_output_notification'] for r in details
                     if 'service_output_notification' in r]
    summary['service_output_notification'] = dict(
        frames_with_unique_wake_and_waker=len(notifications),
        origins=dict(collections.Counter(n['origin'] for n in notifications)),
        unique_kernel_AppleAVD_threads=len({(n['waker']['pid'], n['waker']['tid'])
            for n in notifications if n['origin'] == 'kernel_AppleAVD'}),
        metrics_ns={key: _aggregate([n[key] for n in notifications]) for key in
            ('return_to_wake_ns', 'runnable_ns', 'wake_to_first_io_ns')})
    summary['callback_event_states'] = dict(collections.Counter(r['callback_event_state'] for r in details))
    summary['callback_dispatch'] = dict(
        frames_with_last_runnable=sum(r['last_callback_runnable'] is not None for r in details),
        frames_last_runnable_followed_by_only_running=sum(r.get('last_runnable_followed_by_only_running', False) for r in details),
        runnable_ns=_aggregate([r['last_callback_runnable_ns'] for r in details if r['last_callback_runnable'] is not None]),
        after_runnable_until_callback_ns=_aggregate([r['after_last_runnable_until_callback_ns'] for r in details if r['last_callback_runnable'] is not None]))
    syscall_summary = {}
    for kind in ('condition_wait', 'sync_xpc'):
        events = [s for r in details for s in r['syscalls'] if s['kind'] == kind]
        entry = dict(syscalls=len(events), calls_with_blocked_interval=sum(s['states_ns'].get('Blocked', 0) > 0 for s in events),
            calls_with_wake_edge=sum(bool(s['wake_edges']) for s in events),
            wake_origins=dict(collections.Counter(origin(w) for s in events for e in s['wake_edges'] for w in e['wakers'])))
        if kind == 'condition_wait':
            for key in ('unique_condition_signal', 'signal_matches_unique_kernel_waker', 'wake_inside_signal'):
                entry[key+'_count'] = sum(s[key] for s in events)
        syscall_summary[kind] = entry
    summary['syscalls'] = syscall_summary
    summary['limitations'] = [
        'Blocked time is a thread state, not a measurement of hardware decoder execution.',
        'Wake origins identify immediate kernel wakers, not transitive ownership or causality.',
        'After-runnable execution includes worker work before the callback signpost; it is not a pure dispatch cost.',
        'The service output interval is return to the first recorded output IO syscall on a unique output thread. Its state does not isolate hardware time.',
        'Trace signpost boundaries are exact within the trace clock; raw callback stamps precede their trace end event.']
    return summary, dict(frames=details, excluded_frames=invalid, thread_states=states)
