#!/usr/bin/env python3
"""Synthetic exact timestamp parsing and scheduling-coverage tests."""
import importlib.util
import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('vt_profile', SCRIPTS / 'analyze-vt-profile.py')
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


class XMLTests(unittest.TestCase):
    def table(self, contents):
        temporary = tempfile.TemporaryDirectory(prefix='mav-profile-test-')
        self.addCleanup(temporary.cleanup)
        path = pathlib.Path(temporary.name) / 'trace.xml'
        path.write_text(contents)
        return PROFILE.XMLTable(path)

    def test_structured_metadata_resolves_nested_refs_without_float_rounding(self):
        table = self.table('''<trace-query-result><node><schema name="region-of-interest">
          <col><mnemonic>start-message</mnemonic></col><col><mnemonic>process</mnemonic></col>
          </schema><row><os-log-metadata id="1"><narrative-text id="2">submit_ns=</narrative-text>
          <uint64 id="3">9007199254740993</uint64><narrative-text>work=</narrative-text>
          <uint64>36490447512</uint64></os-log-metadata><process id="4"><pid id="5">42</pid></process></row>
          <row><os-log-metadata ref="1"/><process ref="4"/></row></node></trace-query-result>''')
        rows = list(table.rows('region-of-interest'))
        for row in rows:
            self.assertEqual(table.metadata(row['start-message']), {'submit_ns': 9007199254740993, 'work': 36490447512})
            self.assertEqual(table.child_integer(row['process'], 'pid'), 42)

    def test_formatted_metadata_handles_thousands_separators_and_hex_pointers(self):
        table = self.table('''<root><os-log-metadata id="1"
          fmt="work= 0x8feed  submit_ns= 798,519,728,426,833 status= -12"/></root>''')
        values = table.metadata(table.ids['1'])
        self.assertEqual(values, {'work': 0x8feed, 'submit_ns': 798519728426833, 'status': -12})

    def test_missing_reference_does_not_become_zero(self):
        table = self.table('<root><uint64 ref="missing"/></root>')
        with self.assertRaises(ValueError):
            table.integer(table.root[0])


class CoverageTests(unittest.TestCase):
    def test_clipping_partitions_states_and_explicit_uncovered_gaps(self):
        result = PROFILE.overlap_states(100, 200, [(80, 130, 'Running'), (130, 150, 'Runnable'),
                                                  (160, 250, 'Blocked')])
        self.assertEqual(result, {'Running': 30, 'Runnable': 20, 'uncovered': 10, 'Blocked': 40})
        self.assertEqual(sum(result.values()), 100)

    def test_overlapping_rows_are_ambiguous_not_double_counted(self):
        result = PROFILE.overlap_states(0, 100, [(0, 70, 'Running'), (30, 90, 'Blocked')])
        self.assertEqual(result, {'Running': 30, 'ambiguous': 40, 'Blocked': 20, 'uncovered': 10})
        self.assertEqual(sum(result.values()), 100)

    def test_duplicate_identical_state_records_are_ambiguous(self):
        result = PROFILE.overlap_states(0, 10, [(0, 10, 'Running'), (0, 10, 'Running')])
        self.assertEqual(result, {'ambiguous': 10, 'uncovered': 0})

    def test_absent_thread_is_completely_uncovered(self):
        self.assertEqual(PROFILE.overlap_states(7, 20, []), {'uncovered': 13})

    def test_unknown_state_is_not_known_scheduling_coverage(self):
        summary = PROFILE.summarize_frames([{'submit_thread_states_ns': {'Unknown': 10}}])
        self.assertEqual(summary['fully_covered_frames'], 1)
        self.assertEqual(summary['fully_known_frames'], 0)
        self.assertEqual(summary['submit_thread_states_ns']['Unknown']['sum'], 10)

    def test_other_states_are_preserved(self):
        result = PROFILE.overlap_states(0, 10, [(0, 5, 'Interrupted'), (5, 10, 'Preempted')])
        self.assertEqual(result, {'Interrupted': 5, 'Preempted': 5, 'uncovered': 0})


if __name__ == '__main__':
    unittest.main()
