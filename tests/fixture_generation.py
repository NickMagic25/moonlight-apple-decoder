#!/usr/bin/env python3
"""Small real-encoder bitrate/HDR/import smoke; run separately from timed decoding."""
import argparse
from decimal import Decimal
import hashlib
import json
import pathlib
import subprocess
import tempfile


def check(tool, aomenc, root, codec, variant, gop=6, bitrate_mbps=1.25):
    output = root / f'{codec}-{variant}-gop{gop}-{bitrate_mbps}mbps'
    target_bps = int(Decimal(str(bitrate_mbps)) * 1000000)
    target_kbps = target_bps // 1000
    command = [str(tool), '--codec', codec, '--variant', variant, '--output', str(output),
               '--width', '256', '--height', '144', '--fps', '30', '--frames', '12',
               '--gop', str(gop), '--bitrate-mbps', str(bitrate_mbps)]
    if codec == 'av1':
        command += ['--aomenc', str(aomenc)]
    subprocess.run(command, check=True)
    manifest = json.loads((output / 'manifest.json').read_text())
    payload = (output / 'payload.bin').read_bytes()
    generator = manifest['generator']
    assert generator['settings'] == dict(codec=codec, variant=variant, width=256, height=144,
                                         fps=30, frames=12, gop=gop, bitrate_mbps=bitrate_mbps, chroma='420')
    assert generator['requested_bitrate_mbps'] == bitrate_mbps
    assert generator['content_profile'] == 'seeded-noise-frame-id-v1'
    assert generator['content_seed'] == 0x6d617631
    assert 'requested_bitrate_kbps' not in generator
    assert generator['target_bitrate_bps'] == target_bps
    assert generator['measured_bitrate_bps'] == len(payload) * 8 * 30 / 12
    assert generator['measured_bitrate_mbps'] == generator['measured_bitrate_bps'] / 1000000
    assert manifest['payload_sha256'] == hashlib.sha256(payload).hexdigest()
    assert len(manifest['access_units']) == 12
    assert manifest['bit_depth'] == (10 if variant == 'hdr10' else 8)
    assert manifest['color']['transfer'] == (16 if variant == 'hdr10' else 1)
    assert generator['low_delay_verified']
    assert generator['random_access_count'] >= 2
    assert all(manifest['access_units'][frame]['random_access'] for frame in range(0, 12, gop))
    if gop == 1:
        assert generator['inter_count'] == 0
    else:
        assert generator['inter_count'] > 0
    if codec == 'av1':
        arguments = generator['encoder_settings']['arguments']
        assert f'--target-bitrate={target_kbps}' in arguments
        assert '--end-usage=cbr' in arguments
        assert '--usage=1' in arguments and '--cpu-used=8' in arguments
        for expected in ('--max-intra-rate=300', '--max-inter-rate=300', '--undershoot-pct=10',
                         '--overshoot-pct=10', '--buf-sz=1000', '--buf-initial-sz=500',
                         '--buf-optimal-sz=500', '--drop-frame=0'):
            assert expected in arguments
        assert not any(value.startswith('--cq-level=') for value in arguments)
        assert json.loads((output / 'encoder-arguments.json').read_text()) == arguments
        assert generator['rate_control'] == 'cbr'
    else:
        assert generator['encoder_settings']['average_bitrate_bps'] == target_bps
        assert generator['encoder_settings']['data_rate_limits'] == [target_bps * 3 // 20, 1]
        assert generator['encoder_settings']['realtime'] is False
        assert generator['rate_control'] == 'average_bitrate'
    imported = output / 'imported'
    subprocess.run([str(tool), '--import', str(output / 'manifest.json'), '--output', str(imported)],
                   check=True)
    imported_manifest = json.loads((imported / 'manifest.json').read_text())
    assert imported_manifest['generator'] == generator
    assert imported_manifest['access_units'] == manifest['access_units']
    assert (imported / 'payload.bin').read_bytes() == payload
    return manifest['payload_sha256']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=pathlib.Path, default=pathlib.Path('build/mav-fixture'))
    parser.add_argument('--aomenc', type=pathlib.Path, default=pathlib.Path('.local/aom-build/aomenc'))
    parser.add_argument('--results-dir', type=pathlib.Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='mav-fixture-generation-') as temporary:
        root = args.results_dir.resolve() if args.results_dir else pathlib.Path(temporary)
        root.mkdir(parents=True, exist_ok=True)
        av1_hash = None
        for codec in ('av1', 'hevc'):
            for variant in ('sdr8', 'hdr10'):
                payload_hash = check(args.tool.resolve(), args.aomenc.resolve(), root, codec, variant)
                if codec == 'av1' and variant == 'sdr8':
                    av1_hash = payload_hash
        # AOM's deterministic encoding also verifies that the seeded source
        # does not depend on output paths, wall time, or process randomness.
        assert check(args.tool.resolve(), args.aomenc.resolve(), root / 'repeat', 'av1', 'sdr8') == av1_hash
        check(args.tool.resolve(), args.aomenc.resolve(), root, 'hevc', 'sdr8', gop=1)
        for codec in ('av1', 'hevc'):
            for bitrate_mbps in (50, 100, 250, 350):
                check(args.tool.resolve(), args.aomenc.resolve(), root, codec, 'sdr8', bitrate_mbps=bitrate_mbps)
    print('PASS real AV1/HEVC SDR/HDR bitrate targets, measured payload rates, GOP, and import preservation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
