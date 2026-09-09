#!/usr/bin/env python3
"""Real AV1 hidden/show-existing and multi-frame accounting, checked against libaom."""
import argparse
import array
import hashlib
import json
import os
import pathlib
import platform
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def command(args, log=None):
    args = list(map(str, args))
    print('+', ' '.join(args), flush=True)
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    if log:
        pathlib.Path(log).write_text(result.stdout + result.stderr)
    elif result.stdout:
        print(result.stdout, end='')
    if result.returncode:
        raise RuntimeError(f'{args[0]} exited {result.returncode}: {result.stderr[-2000:]}')
    return result.stdout.strip()


def source(path, depth):
    with path.open('wb') as out:
        for frame in range(48):
            samples = [32 + (x+y+frame*3) % 160 if (x-frame) % 64 > 8 else 220
                       for y in range(144) for x in range(256)]
            samples += [100] * 9216 + [140] * 9216
            if depth == 8:
                out.write(bytes(samples))
            else:
                pixels = array.array('H', (sample*4 for sample in samples))
                if sys.byteorder != 'little':
                    pixels.byteswap()
                out.write(pixels.tobytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default='build')
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--depths', default='8,10')
    args = parser.parse_args()
    depths = [int(depth) for depth in args.depths.split(',')]
    if not depths or any(depth not in (8, 10) for depth in depths):
        parser.error('--depths must contain 8 and/or 10')
    results_dir = ROOT/'results/av1-accounting'
    results_dir.mkdir(parents=True, exist_ok=True)
    status = {'schema_version': 1, 'test': 'av1-hidden-existing-accounting', 'results': []}
    try:
        if platform.system() != 'Darwin':
            raise RuntimeError('physical Apple VideoToolbox hardware is required')
        build = (ROOT/args.build_dir).resolve()
        cmake = os.environ.get('CMAKE', 'cmake')
        encoder = pathlib.Path(os.environ.get('AOMENC', ROOT/'.local/aom-build/aomenc')).resolve()
        decoder = pathlib.Path(os.environ.get('AOMDEC', ROOT/'.local/aom-build/aomdec')).resolve()
        if not encoder.is_file() or not decoder.is_file():
            raise RuntimeError('run ./scripts/bootstrap-aom.sh or set AOMENC and AOMDEC')
        if not args.skip_build:
            command([cmake, '-S', ROOT, '-B', build, '-DCMAKE_BUILD_TYPE=Release'])
            command([cmake, '--build', build, '--target', 'mav-av1-accounting', '--parallel', '4'])
        for depth in depths:
            output = ROOT/f'fixtures/generated/av1-accounting-{depth}'
            output.mkdir(parents=True, exist_ok=True)
            raw, encoded, reference = output/'source.yuv', output/'encoded.ivf', output/'reference.i420'
            source(raw, depth)
            encoder_args = ['--codec=av1', '--ivf', '--i420', '--passes=1', '--usage=0', '--cpu-used=6',
                            '--threads=2', '--lag-in-frames=25', '--auto-alt-ref=1', '--min-gf-interval=16',
                            '--max-gf-interval=16', '--gf-min-pyr-height=4', '--gf-max-pyr-height=4',
                            '--end-usage=q', '--cq-level=24', '--disable-warning-prompt', '--width=256',
                            '--height=144', '--fps=30/1', '--limit=48', f'--bit-depth={depth}',
                            f'--input-bit-depth={depth}', '--kf-max-dist=48', '--kf-min-dist=48',
                            f'--output={encoded}', str(raw)]
            command([encoder, *encoder_args], output/'encoder.log')
            command([decoder, '--rawvideo', '--i420', f'--output-bit-depth={depth}',
                     f'--output={reference}', encoded], output/'reference.log')
            result_file = results_dir/f'{depth}bit.json'
            command([build/'mav-av1-accounting', encoded, reference, result_file], output/'native.log')
            record = json.loads(result_file.read_text())
            record.update(fixture_sha256=hashlib.sha256(encoded.read_bytes()).hexdigest(),
                          source_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                          reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest())
            result_file.write_text(json.dumps(record, indent=2)+'\n')
            provenance = dict(encoder=command([encoder, '--help'], output/'encoder-help.txt').split('Included encoders:')[-1].strip(),
                              encoder_arguments=encoder_args, depth=depth,
                              fixture_sha256=record['fixture_sha256'], library_revision=command(['git', 'rev-parse', 'HEAD']),
                              os=platform.platform(), architecture=platform.machine(),
                              model=command(['sysctl', '-n', 'machdep.cpu.brand_string']),
                              sdk=command(['xcrun', '--show-sdk-version']))
            (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
            status['results'].append(record)
        status['status'] = 'PASS'
    except Exception as error:
        status['status'] = 'FAIL'
        status['reason'] = str(error)
    (results_dir/'summary.json').write_text(json.dumps(status, indent=2)+'\n')
    print(json.dumps(status, indent=2))
    return 0 if status['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
