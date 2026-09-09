"""Derive equivalent caller-visible timings from raw, unmodified traces."""
import csv


def moonlight_timings(rows):
    """Whole-trial arithmetic means, including cold/warmup outputs.

    Match AppleVideoDecoder::receive/updateOverlay for both native metrics.
    The public metric is only a proxy for the regular Qt/FFmpeg overlay: the
    benchmark does not measure the app's queue, frame wrapping or live window.
    Keep integer sums/counts so repetitions can be weighted by actual outputs.
    """
    outputs = [r for r in rows if r['status'] == 0 and r['displayed_outputs'] == 1]
    native = [r['callback_ns'] - r['vt_submit_ns'] for r in outputs
              if r['internal_samples'] == 1 and not r['show_existing']
              and (r['trace_valid'] & 10) == 10 and r['callback_ns'] >= r['vt_submit_ns']]
    # A completion may run before the backend records API return. Keep an
    # independent population: missing return timestamps are not zero-time calls.
    submission = [r['vt_return_ns'] - r['vt_submit_ns'] for r in outputs
                  if r['internal_samples'] == 1 and not r['show_existing']
                  and (r['trace_valid'] & 6) == 6 and 'vt_return_ns' in r
                  and r['vt_return_ns'] >= r['vt_submit_ns']]
    public = [r['sink_entry_ns'] - r['scheduled_arrival_ns'] for r in outputs
              if r['trace_valid'] & 16 and r['sink_entry_ns'] >= r['scheduled_arrival_ns']]
    def mean(values):
        count, total = len(values), sum(values)
        return dict(sample_count=count, total_ns=total, mean_ms=total / count / 1e6 if count else None)
    return dict(native_vt=mean(native), native_submission=mean(submission), public_queue_proxy=mean(public))


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(count=0, mean=None, median=None, p95=None, p99=None, min=None, max=None)
    def quantile(fraction):
        index = fraction * (len(values) - 1)
        low = int(index)
        return values[low] + (index - low) * (values[min(low + 1, len(values) - 1)] - values[low])
    return dict(count=len(values), mean=sum(values)/len(values), median=quantile(.5),
                p95=quantile(.95), p99=quantile(.99), min=values[0], max=values[-1])


def caller_timings(path, result):
    """Return supplemental metrics; never replace or filter accounting totals.

    Benchmark generator IDs are sequential from zero. Each CSV row retains the
    original status. Only genuine new single-sample images enter latency stats;
    lost/rejected/cancelled/no-display/existing events stay in original totals.
    """
    if not path.is_file() or not result.get('run_seconds'):
        return {}
    with path.open(newline='') as source:
        rows = [{key: int(value) for key, value in row.items()}
                for row in csv.DictReader(source)]
    if not rows:
        return {}
    if 'sink_entry_ns' not in rows[0]:
        return dict(public_complete_au_to_output_ns=result.get('complete_au_to_output_ns'),
                    public_output_boundary='FFmpeg avcodec_receive_frame return',
                    cold_public_complete_au_to_output_ns=result.get('cold_complete_au_to_output_ns'))
    outputs = [r for r in rows if r['status'] == 0 and r['displayed_outputs'] == 1]
    first = {}
    for row in outputs:
        generation = row['generation']
        if generation not in first or row['admission_ns'] < first[generation]['admission_ns']:
            first[generation] = row
    cold_ids = {(r['generation'], r['frame_id']) for r in first.values()}
    steady = [r for r in outputs if r['frame_id'] >= result['warmup_frames']
              and (r['generation'], r['frame_id']) not in cold_ids
              and r['internal_samples'] == 1 and not r['show_existing']
              and r['trace_valid'] & 16 and r['sink_entry_ns'] >= r['scheduled_arrival_ns']]
    cold = [r for r in first.values() if r['trace_valid'] & 16
            and r['sink_entry_ns'] >= r['scheduled_arrival_ns']]
    initial = min(rows, key=lambda r: r['admission_ns'])
    return dict(
        moonlight_decode_time=moonlight_timings(rows),
        public_complete_au_to_output_ns=distribution([r['sink_entry_ns']-r['scheduled_arrival_ns'] for r in steady]),
        public_output_boundary='Native public completion callback entry in harness',
        cold_public_complete_au_to_output_ns=distribution([r['sink_entry_ns']-r['scheduled_arrival_ns'] for r in cold]),
        cold_population='First successful displayed output in each generation; may follow a cancelled initial submission',
        initial_submission_frame_id=initial['frame_id'],
        initial_submission_status=initial['status'],
        initial_submission_terminal_ns=initial['sink_entry_ns']-initial['scheduled_arrival_ns']
            if initial['trace_valid'] & 16 else None,
        submit_entry_to_vt_submit_ns=distribution([r['vt_submit_ns']-r['admission_ns'] for r in steady
            if r['trace_valid'] & 2 and r['vt_submit_ns'] >= r['admission_ns']]),
        post_parser_to_vt_submit_ns=distribution([r['vt_submit_ns']-r['preparation_end_ns'] for r in steady
            if r['trace_valid'] & 3 == 3 and r['vt_submit_ns'] >= r['preparation_end_ns']]),
        derivation='Supplemental distributions from raw CSV; warmup and first output per generation excluded '
                   'from steady distributions. Moonlight arithmetic means include all eligible outputs. '
                   'Original totals and internal VT callback endpoint remain unchanged.')
