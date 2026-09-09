"""Synthetic checks for thread coverage and exact wait/signal qualifications."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from vt_wait_states import analyze_state_dependencies
from vt_wait_states import read_target_states


def row(start, end, state, wakers=()):
    return dict(start=start, end=end, state=state, pid=1, note='', wakers=list(wakers))


def frame(**changes):
    value = dict(frame_id=9, steady=True, submit_tid=10, callback_tid=11,
        trace_call_start_ns=100, trace_call_end_ns=200, trace_frame_end_ns=300)
    value.update(changes)
    return value


class StateEvidenceTests(unittest.TestCase):
    def analyze(self, states, frames=None, calls=None):
        return analyze_state_dependencies(None, frames or [frame()], 1, 2,
                                           calls, states=states)

    def test_gap_remains_uncovered(self):
        summary, _ = self.analyze({10: [row(100, 150, 'Running')],
                                  11: [row(200, 301, 'Running')]})
        call = summary['roles']['submit_call']
        self.assertEqual(call['states_ns']['uncovered']['sum'], 50)
        self.assertEqual(call['fully_covered_frames'], 0)

    def test_structured_waker_refs_preserve_identity(self):
        columns = ''.join('<col><mnemonic>'+n+'</mnemonic></col>' for n in
                          ('start', 'process', 'thread', 'duration', 'state', 'note'))
        source = '<trace-query-result><node><schema name="thread-state">'+columns+'</schema>'
        source += '''<row><start-time>250</start-time>
            <process id="p"><pid>2</pid></process>
            <thread><tid>20</tid><process ref="p"/></thread><duration>10</duration>
            <state>Runnable</state><narrative fmt="made runnable by AppleAVD">
            <thread id="w" fmt="AppleAVD (0x1cc) (kernel, pid: 0)">
            <tid>460</tid><process id="k"><pid>0</pid></process></thread></narrative></row>
            <row><start-time>350</start-time><process ref="p"/>
            <thread><tid>20</tid><process ref="p"/></thread><duration>10</duration>
            <state>Runnable</state><narrative><thread ref="w"/></narrative></row>
            </node></trace-query-result>'''
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'states.xml'
            path.write_text(source)
            states = read_target_states(path, 1, 2)
        self.assertEqual(states[20][0]['wakers'], states[20][1]['wakers'])
        self.assertEqual(states[20][0]['wakers'][0]['pid'], 0)
        self.assertEqual(states[20][0]['wakers'][0]['tid'], 460)
        self.assertTrue(states[20][0]['wakers'][0]['label'].startswith('AppleAVD '))

    def test_duplicate_states_are_ambiguous_not_double_counted(self):
        summary, _ = self.analyze({10: [row(100, 200, 'Running'), row(150, 175, 'Running')]})
        states = summary['roles']['submit_call']['states_ns']
        self.assertEqual(states['ambiguous']['sum'], 25)
        self.assertEqual(states['Running']['sum'], 75)

    def test_nonsequential_callback_excluded(self):
        summary, details = self.analyze({}, [frame(trace_frame_end_ns=150)])
        self.assertEqual(summary['excluded_nonsequential_frames'], 1)
        self.assertEqual(summary['analyzed_frames'], 0)
        self.assertEqual(len(details['excluded_frames']), 1)

    def test_callback_dispatch_requires_contiguous_running(self):
        states = {10: [row(100, 300, 'Running')], 11: [row(200, 240, 'Blocked'),
            row(240, 250, 'Runnable'), row(250, 301, 'Running')]}
        summary, _ = self.analyze(states)
        dispatch = summary['callback_dispatch']
        self.assertEqual(dispatch['runnable_ns']['median'], 10)
        self.assertEqual(dispatch['after_runnable_until_callback_ns']['median'], 50)
        self.assertEqual(dispatch['frames_last_runnable_followed_by_only_running'], 1)
        states[11][2] = row(260, 301, 'Running')
        summary, _ = self.analyze(states)
        self.assertEqual(summary['callback_dispatch']['frames_last_runnable_followed_by_only_running'], 0)

    def test_wake_beginning_before_window_is_not_recounted(self):
        summary, _ = self.analyze({10: [row(90, 110, 'Runnable', [dict(pid=2, tid=20)]),
                                      row(110, 301, 'Running')]})
        self.assertEqual(summary['roles']['submit_call']['wake_origins'], {})
        self.assertEqual(summary['roles']['submit_call']['states_ns']['Runnable']['sum'], 10)

    def test_condition_requires_address_and_waker_identity(self):
        states = {10: [row(100, 120, 'Running'), row(120, 180, 'Blocked'),
            row(180, 190, 'Runnable', [dict(pid=1, tid=11)]), row(190, 301, 'Running')],
            11: [row(100, 301, 'Running')]}
        wait = dict(start_ns=115, end_ns=195, pid=1, tid=10, args=[2**60+1])
        signal = dict(start_ns=175, end_ns=185, pid=1, tid=11, args=[2**60+1])
        calls = [dict(frame_id=9, condition_waits=[wait], condition_signals=[signal])]
        summary, _ = self.analyze(states, calls=calls)
        cv = summary['syscalls']['condition_wait']
        self.assertEqual(cv['unique_condition_signal_count'], 1)
        self.assertEqual(cv['signal_matches_unique_kernel_waker_count'], 1)
        self.assertEqual(cv['wake_inside_signal_count'], 1)
        signal['args'] = [2**60+2]
        summary, _ = self.analyze(states, calls=calls)
        self.assertEqual(summary['syscalls']['condition_wait']['unique_condition_signal_count'], 0)
        signal['args'], signal['tid'] = [2**60+1], 12
        summary, _ = self.analyze(states, calls=calls)
        cv = summary['syscalls']['condition_wait']
        self.assertEqual(cv['unique_condition_signal_count'], 1)
        self.assertEqual(cv['signal_matches_unique_kernel_waker_count'], 0)
        wait['args'], signal['args'] = [None], [None]
        summary, _ = self.analyze(states, calls=calls)
        self.assertEqual(summary['syscalls']['condition_wait']['unique_condition_signal_count'], 0)

    def test_service_output_requires_unique_thread_and_in_window_io(self):
        calls = [dict(frame_id=9, service_output_io=[dict(pid=2, tid=20, start_ns=280)])]
        summary, _ = self.analyze({20: [row(200, 250, 'Blocked'),
            row(250, 260, 'Runnable', [dict(pid=0, tid=460, label='AppleAVD (0x1cc) (kernel, pid: 0)')]),
            row(260, 280, 'Running')]}, calls=calls)
        role = summary['roles']['service_output_before_first_io']
        self.assertEqual(role['duration_ns']['sum'], 80)
        self.assertEqual(role['states_ns']['Blocked']['sum'], 50)
        self.assertEqual(role['fully_covered_frames'], 1)
        notification = summary['service_output_notification']
        self.assertEqual(notification['origins'], {'kernel_AppleAVD': 1})
        self.assertEqual(notification['unique_kernel_AppleAVD_threads'], 1)
        self.assertEqual(notification['metrics_ns']['return_to_wake_ns']['sum'], 50)
        self.assertEqual(notification['metrics_ns']['runnable_ns']['sum'], 10)
        calls[0]['service_output_io'].append(dict(pid=2, tid=21, start_ns=290))
        summary, _ = self.analyze({}, calls=calls)
        self.assertEqual(summary['service_output_interval_selection']['ambiguous_output_threads'], 1)
        self.assertEqual(summary['roles']['service_output_before_first_io']['frames'], 0)


if __name__ == '__main__':
    unittest.main()
