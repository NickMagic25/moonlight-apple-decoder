#!/usr/bin/env python3
"""Add Moonlight decode averages to saved reports without running any decoder.

Every timed JSON and CSV is verified against the original results.json before
rendering. The original analysis, verdicts, plan, native results, and traces are
left unchanged. report-original.md preserves the pre-refresh Markdown, while
moonlight-decode-times.json records the supplemental derivation and provenance.
"""
import argparse
import copy
import csv
import datetime
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(data):
    def invalid(value):
        raise ValueError('non-finite JSON number: ' + value)
    return json.loads(data.decode('utf-8'), parse_constant=invalid)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def checked_digest(value, description):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('missing or invalid SHA-256: ' + description)
    return value


def evidence_path(directory, value):
    if not isinstance(value, str) or not value or pathlib.Path(value).is_absolute():
        raise ValueError('evidence path must be relative to the results directory')
    path = (directory / value).resolve()
    try:
        path.relative_to(directory)
    except ValueError:
        raise ValueError('evidence path escapes the results directory: ' + value)
    return path


def verified_bytes(directory, record, field):
    expected = checked_digest(record.get(field + '_sha256'), field)
    path = evidence_path(directory, record.get(field))
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(field + ' changed since execution: ' + str(path))
    return data


def prior_report(directory, original_bytes, results_sha256):
    """Accept only the original report or an intact prior refresh of this source."""
    report = directory / 'report.md'
    backup = directory / 'report-original.md'
    companion = directory / 'moonlight-decode-times.json'
    original_sha256 = digest(original_bytes)
    if backup.exists() and backup.read_bytes() != original_bytes:
        raise ValueError('report-original.md differs from the source report: ' + str(backup))
    if not report.exists():
        if backup.exists() or companion.exists():
            raise ValueError('incomplete previous report refresh: ' + str(directory))
        return
    current_sha256 = digest(report.read_bytes())
    if current_sha256 == original_sha256:
        return
    if not backup.is_file() or not companion.is_file():
        raise ValueError('existing report differs from source without verified refresh provenance: ' + str(report))
    metadata = read_json(companion.read_bytes())
    provenance = metadata.get('moonlight_report_derivation', {})
    if (metadata.get('report_sha256') != current_sha256
            or provenance.get('source_results_sha256') != results_sha256
            or provenance.get('original_report_sha256') != original_sha256):
        raise ValueError('previous report refresh provenance does not match source: ' + str(directory))


def atomic_bytes(path, data):
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.', delete=False) as temporary:
        temporary.write(data)
        temporary_path = pathlib.Path(temporary.name)
    try:
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-dir', required=True,
                        help='Original local run directory containing results.json and its raw CSV/JSON files')
    parser.add_argument('--report-dir', help='Report destination; defaults to --results-dir')
    args = parser.parse_args(argv)
    source = pathlib.Path(args.results_dir).resolve()
    destination = pathlib.Path(args.report_dir).resolve() if args.report_dir else source
    try:
        source_results = source / 'results.json'
        source_bytes = source_results.read_bytes()
        source_sha256 = digest(source_bytes)
        original = read_json(source_bytes)
        if not isinstance(original, dict) or not isinstance(original.get('cases'), list):
            raise ValueError('results.json has no case list')
        checked_digest(original.get('analysis_sha256'), 'original analysis_sha256')
        backup = source / 'report-original.md'
        original_report = backup if backup.is_file() else source / 'report.md'
        original_report_bytes = original_report.read_bytes()
        prior_report(source, original_report_bytes, source_sha256)
        if destination.exists() and not destination.is_dir():
            raise ValueError('report destination is not a directory')
        target_results = destination / 'results.json'
        if target_results.exists() and target_results.read_bytes() != source_bytes:
            raise ValueError('destination results.json differs from original analysis')
        prior_report(destination, original_report_bytes, source_sha256)

        # Importing the runner exposes its renderer only. Its main(), analyze(),
        # build, fixture, correctness, and timing entry points are never called.
        scripts = pathlib.Path(__file__).resolve().parent
        runner_path = scripts / 'compare-decoders.py'
        spec = importlib.util.spec_from_file_location('saved_decoder_report_renderer', runner_path)
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        from benchmark_analysis import moonlight_timings

        result = copy.deepcopy(original)
        timed_count = 0
        for case in result['cases']:
            if not isinstance(case.get('runs'), list):
                raise ValueError('case has no run list')
            for run in case['runs']:
                if run.get('phase') != 'timed':
                    continue
                native = read_json(verified_bytes(source, run, 'result_file'))
                if canonical(native) != canonical(run.get('native')):
                    raise ValueError('native JSON differs from saved analysis: ' + run['result_file'])
                trace = verified_bytes(source, run, 'csv_file')
                reader = csv.DictReader(io.StringIO(trace.decode('utf-8'), newline=''))
                required = {'status', 'displayed_outputs', 'internal_samples', 'show_existing',
                            'trace_valid', 'vt_submit_ns', 'vt_return_ns', 'callback_ns',
                            'scheduled_arrival_ns', 'sink_entry_ns'}
                if not reader.fieldnames or not required.issubset(reader.fieldnames):
                    raise ValueError('timed trace lacks Moonlight timing columns: ' + run['csv_file'])
                if len(set(reader.fieldnames)) != len(reader.fieldnames):
                    raise ValueError('duplicate CSV columns: ' + run['csv_file'])
                rows = [{key: int(value) for key, value in row.items()} for row in reader]
                run.setdefault('derived', {})['moonlight_decode_time'] = moonlight_timings(rows)
                timed_count += 1
        if not timed_count:
            raise ValueError('results.json contains no timed records')

        # An explicit comparison makes the report-only scope reviewable: remove
        # the added field and demand that every original record and verdict,
        # including all correctness results, is identical to the saved analysis.
        unchanged = copy.deepcopy(result)
        for old_case, new_case in zip(original['cases'], unchanged['cases']):
            for old_run, new_run in zip(old_case['runs'], new_case['runs']):
                if new_run.get('phase') == 'timed':
                    if 'derived' in old_run:
                        new_run['derived'] = copy.deepcopy(old_run['derived'])
                    else:
                        new_run.pop('derived', None)
        if canonical(unchanged) != canonical(original):
            raise ValueError('report derivation changed original analysis')
        result['moonlight_report_derivation'] = dict(
            derived_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source_results_file=str(source_results), source_results_sha256=source_sha256,
            original_report_file=str(original_report), original_report_sha256=digest(original_report_bytes),
            source_analysis_sha256=original['analysis_sha256'],
            refresh_script_sha256=digest(pathlib.Path(__file__).read_bytes()),
            report_generator_sha256=digest(runner_path.read_bytes()),
            timing_derivation_sha256=digest((scripts / 'benchmark_analysis.py').read_bytes()),
            verified_timed_records=timed_count,
            original_results_unchanged=True, original_correctness_unchanged=True,
            execution='Offline derivation from saved JSON and CSV; no tests, decoders, encoders, builds, or benchmarks run.')

        # Render into temporary storage only after all source integrity checks.
        # Validate both products before replacing any destination report files.
        with tempfile.TemporaryDirectory(prefix='moonlight-report-refresh-') as staging_name:
            staging = pathlib.Path(staging_name)
            runner.report_markdown(result, staging / 'report.md')
            rendered = (staging / 'report.md').read_bytes()
            companion_bytes = (staging / 'moonlight-decode-times.json').read_bytes()
            companion = read_json(companion_bytes)
            if (companion.get('report_sha256') != digest(rendered)
                    or companion.get('moonlight_report_derivation') != result['moonlight_report_derivation']):
                raise ValueError('renderer omitted or changed report provenance')
        if source_results.read_bytes() != source_bytes or original_report.read_bytes() != original_report_bytes:
            raise ValueError('source analysis or original report changed during derivation')
        destination.mkdir(parents=True, exist_ok=True)
        if not target_results.exists():
            atomic_bytes(target_results, source_bytes)
        target_backup = destination / 'report-original.md'
        if not target_backup.exists():
            atomic_bytes(target_backup, original_report_bytes)
        atomic_bytes(destination / 'report.md', rendered)
        atomic_bytes(destination / 'moonlight-decode-times.json', companion_bytes)
        print(f'Updated {destination / "report.md"} from {timed_count} verified timed records.')
        print(f'Supplemental machine-readable report: {destination / "moonlight-decode-times.json"}')
        print('Original results and correctness evidence preserved; no tests or benchmarks were run.')
        return 0
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, OverflowError, ImportError, AttributeError) as error:
        print('Report refresh stopped: ' + str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
