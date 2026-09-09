#!/usr/bin/env python3
"""Small real-encoder bitrate/HDR/import smoke; run separately from timed decoding."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile


def check(tool, aomenc, root, codec, variant, gop=6):
    output = root / f'{codec}-{variant}-gop{gop}'
    command = [str(tool), '--codec', codec, '--variant', variant, '--output', str(output),
               '--width', '256', '--height', '144', '--fps', '30', '--frames', '12',
               '--gop', str(gop), '--bitrate-kbps', '1000']
    if codec == 'av1':
        command += ['--aomenc', str(aomenc)]
    subprocess.run(command, check=True)
    manifest = json.loads((output / 'manifest.json').read_text())
    payload = (output / 'payload.bin').read_bytes()
    generator = manifest['generator']
    assert generator['settings'] == dict(codec=codec, variant=variant, width=256, height=144,
                                         fps=30, frames=12, gop=gop, bitrate_kbps=1000, chroma='420')
    assert generator['requested_bitrate_kbps'] == 1000
    assert generator['target_bitrate_bps'] == 1000000
    assert generator['measured_bitrate_bps'] == len(payload) * 8 * 30 / 12
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
        assert '--target-bitrate=1000' in arguments
        assert '--end-usage=vbr' in arguments
        assert not any(value.startswith('--cq-level=') for value in arguments)
        assert json.loads((output / 'encoder-arguments.json').read_text()) == arguments
        assert generator['rate_control'] == 'vbr'
    else:
        assert generator['encoder_settings']['average_bitrate_bps'] == 1000000
        assert generator['rate_control'] == 'average_bitrate'
    imported = output / 'imported'
    subprocess.run([str(tool), '--import', str(output / 'manifest.json'), '--output', str(imported)],
                   check=True)
    imported_manifest = json.loads((imported / 'manifest.json').read_text())
    assert imported_manifest['generator'] == generator
    assert imported_manifest['access_units'] == manifest['access_units']
    assert (imported / 'payload.bin').read_bytes() == payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', type=pathlib.Path, default=pathlib.Path('build/mav-fixture'))
    parser.add_argument('--aomenc', type=pathlib.Path, default=pathlib.Path('.local/aom-build/aomenc'))
    parser.add_argument('--results-dir', type=pathlib.Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='mav-fixture-generation-') as temporary:
        root = args.results_dir.resolve() if args.results_dir else pathlib.Path(temporary)
        root.mkdir(parents=True, exist_ok=True)
        for codec in ('av1', 'hevc'):
            for variant in ('sdr8', 'hdr10'):
                check(args.tool.resolve(), args.aomenc.resolve(), root, codec, variant)
        check(args.tool.resolve(), args.aomenc.resolve(), root, 'hevc', 'sdr8', gop=1)
    print('PASS real AV1/HEVC SDR/HDR bitrate targets, measured payload rates, GOP, and import preservation')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
