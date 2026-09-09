#!/usr/bin/env python3
"""Protect wait attribution from double-counted RPCs and false signal matches."""
import importlib.util
import pathlib
import sys
import unittest
import xml.etree.ElementTree as ET

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('vt_waits', SCRIPTS / 'analyze-vt-waits.py')
WAITS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WAITS)


def syscall(start, end, stack=(), address=None):
    return {'start_ns': start, 'end_ns': end, 'stack': stack, 'args': [address, 0, 0, 0]}


class RPCPairTests(unittest.TestCase):
    def test_two_mach_syscalls_form_one_rpc_not_two(self):
        send = syscall(10, 20, ('mach_msg2_trap', '_dispatch_mach_msg_send', 'xpc_connection_send_message_with_reply_sync'))
        receive = syscall(22, 80, ('mach_msg2_trap', 'mach_msg_overwrite', 'xpc_connection_send_message_with_reply_sync'))
        pair = WAITS.classify_rpc_pair([receive, send])
        self.assertEqual(pair['logical_rpc_count'], 1)
        self.assertEqual(pair['receive']['end_ns']-pair['send']['start_ns'], 70)

    def test_unrelated_mach_or_two_sends_do_not_qualify(self):
        send = syscall(10, 20, ('_dispatch_mach_msg_send', 'xpc_connection_send_message_with_reply_sync'))
        self.assertIsNone(WAITS.classify_rpc_pair([send, syscall(22, 80, ('mach_msg_overwrite',))]))
        self.assertIsNone(WAITS.classify_rpc_pair([send, syscall(22, 80, send['stack'])]))

    def test_overlap_and_extra_rpc_rows_are_not_silently_paired(self):
        send = syscall(10, 30, ('_dispatch_mach_msg_send', 'xpc_connection_send_message_with_reply_sync'))
        receive = syscall(22, 80, ('mach_msg_overwrite', 'xpc_connection_send_message_with_reply_sync'))
        self.assertIsNone(WAITS.classify_rpc_pair([send, receive]))
        self.assertIsNone(WAITS.classify_rpc_pair([send, receive, receive]))

    def test_symbol_alias_is_exact_and_does_not_guess_adjacent_address(self):
        values = WAITS.StreamValues({'0x1234': 'IOConnectCallMethod'})
        self.assertEqual(values.value(ET.fromstring('<frame name="0x1234"/>')), 'IOConnectCallMethod')
        self.assertEqual(values.value(ET.fromstring('<frame name="0x1235"/>')), '0x1235')


class ConditionTests(unittest.TestCase):
    def test_same_object_and_wait_interval_are_both_required(self):
        wait = syscall(100, 200, address=0x10000000000001)
        correct = syscall(180, 190, address=0x10000000000001)
        wrong_object = syscall(180, 190, address=0x10000000000002)
        too_early = syscall(80, 90, address=0x10000000000001)
        too_late = syscall(201, 210, address=0x10000000000001)
        self.assertEqual(WAITS.matching_condition_signals(wait, [wrong_object, too_early, correct, too_late]), [correct])

    def test_missing_address_never_matches_and_multiple_signals_remain_visible(self):
        self.assertEqual(WAITS.matching_condition_signals(syscall(0, 10), [syscall(2, 3)]), [])
        signals = [syscall(2, 3, address=7), syscall(5, 6, address=7)]
        self.assertEqual(len(WAITS.matching_condition_signals(syscall(0, 10, address=7), signals)), 2)


class PartialCaptureTests(unittest.TestCase):
    def fixture(self):
        run = {'frames': [{'frame_id': n} for n in (2, 3, 4)],
               'unjoined': [{'frame_id': n, 'reason': 'missing call/frame region'} for n in (0, 1, 5)],
               'unmatched_regions': []}
        aggregate = {'join_qualified': False, 'exact_joins': 3, 'csv_rows': 6,
                     'accounting_errors': [], 'extra_regions': {},
                     'join_errors': ['unmatched signposts or CSV frames']}
        return run, aggregate

    def test_boundary_only_subset_keeps_full_run_unqualified(self):
        run, aggregate = self.fixture()
        result = WAITS.qualify_joined_subset(run, aggregate)
        self.assertTrue(result['exact_subset_qualified'])
        self.assertTrue(result['partial_capture'])
        self.assertFalse(result['full_run_join_qualified'])
        self.assertEqual(result['exact_joined_frames'], 3)

    def test_interior_gap_and_payload_failure_are_rejected(self):
        run, aggregate = self.fixture()
        run['unjoined'][0]['frame_id'] = 3
        with self.assertRaisesRegex(ValueError, 'interior gap'):
            WAITS.qualify_joined_subset(run, aggregate)
        run, aggregate = self.fixture()
        run['unjoined'][0] = {'frame_id': 0, 'reasons': ['callback payload mismatch']}
        with self.assertRaisesRegex(ValueError, 'payload'):
            WAITS.qualify_joined_subset(run, aggregate)

    def test_accounting_failure_is_not_excused_by_partial_capture(self):
        run, aggregate = self.fixture()
        aggregate['accounting_errors'] = ['loss or reset']
        with self.assertRaisesRegex(ValueError, 'accounting'):
            WAITS.qualify_joined_subset(run, aggregate)

    def test_missing_interior_id_is_rejected_even_if_omission_list_is_incomplete(self):
        run, aggregate = self.fixture()
        run['frames'] = [{'frame_id': 2}, {'frame_id': 4}, {'frame_id': 5}]
        with self.assertRaisesRegex(ValueError, 'interior gap'):
            WAITS.qualify_joined_subset(run, aggregate)


if __name__ == '__main__':
    unittest.main()
