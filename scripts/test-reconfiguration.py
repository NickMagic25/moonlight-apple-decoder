#!/usr/bin/env python3
"""Test real AV1/HEVC format changes using local Qt probes and generated fixtures."""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PROBES = ('AV1Main8', 'AV1Main10', 'HEVCMain', 'HEVCMain10')


def command(args):
    args = list(map(str, args))
    print('+', ' '.join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def av1_without_array_padding(data):
    """Trim only unframed all-zero array padding at a complete sized-OBU boundary.

    Trailing zero bytes inside a declared OBU payload remain part of that OBU.
    The native parser subsequently validates actual supported codec syntax.
    """
    position = 0
    count = 0
    while position < len(data):
        start = position
        header = data[position]
        if header == 0:
            if not count or any(data[position:]):
                raise ValueError('AV1 probe has invalid nonzero bytes after its final OBU')
            return data[:position]
        if header & 0x81 or not header & 2 or ((header >> 3) & 15) in (0, 9, 10, 11, 12, 13, 14):
            raise ValueError(f'AV1 probe has an invalid explicitly sized OBU header at {position}')
        position += 1
        if header & 4:
            if position >= len(data) or data[position] & 7:
                raise ValueError('AV1 probe has a truncated or invalid OBU extension')
            position += 1
        size = 0
        for index in range(8):
            if position >= len(data):
                raise ValueError('AV1 probe has a truncated OBU size')
            byte = data[position]
            position += 1
            size |= (byte & 127) << (7 * index)
            if not byte & 128:
                break
        else:
            raise ValueError('AV1 probe has an overlong OBU size')
        if size > len(data) - position:
            raise ValueError(f'AV1 probe OBU at {start} exceeds the array')
        position += size
        count += 1
    if not count:
        raise ValueError('empty AV1 probe')
    return data


def extract_probes(qt_dir, probe_dir):
    candidates = [qt_dir/'app/streaming/video'/name
                  for name in ('ffmpeg_videosamples.cpp', 'ffmpeg_videosamples.h')]
    sources = []
    for path in candidates:
        if path.is_file():
            raw = path.read_bytes()
            if len(raw) > 4 * 1024 * 1024:
                raise ValueError(f'probe source exceeds 4 MiB: {path}')
            sources.append((path, raw))
    if not sources:
        raise FileNotFoundError('set MOONLIGHT_QT_DIR to the actual local Moonlight Qt checkout containing app/streaming/video/ffmpeg_videosamples.cpp')
    probe_dir.mkdir(parents=True, exist_ok=True)
    provenance = []
    for name in PROBES:
        pattern = (r'\bconst\s+uint8_t\s+FFmpegVideoDecoder::k_' + re.escape(name)
                   + r'TestFrame\s*\[\s*\]\s*=\s*\{(.*?)\}\s*;')
        matches = [(path, raw, match.group(1)) for path, raw in sources
                   for match in re.finditer(pattern, raw.decode('utf-8'), re.DOTALL)]
        if len(matches) != 1:
            raise ValueError(f'expected exactly one actual Qt {name} probe array, found {len(matches)}')
        path, source, initializer = matches[0]
        initializer = re.sub(r'/\*.*?\*/|//[^\n]*', '', initializer, flags=re.DOTALL)
        tokens = [token.strip() for token in initializer.split(',') if token.strip()]
        if not tokens or any(not re.fullmatch(r'0[xX][0-9A-Fa-f]{1,2}|[0-9]{1,3}', token) for token in tokens):
            raise ValueError(f'unsupported nonliteral byte initializer in {name}')
        original = bytes(int(token, 16 if token.lower().startswith('0x') else 10) for token in tokens)
        payload = av1_without_array_padding(original) if name.startswith('AV1') else original
        output = probe_dir/f'{name}.bin'
        output.write_bytes(payload)
        provenance.append(dict(name=name, source_path=str(path),
                               source_sha256=hashlib.sha256(source).hexdigest(),
                               original_array_bytes=len(original), payload_bytes=len(payload),
                               unframed_av1_padding_removed=len(original)-len(payload),
                               original_array_sha256=hashlib.sha256(original).hexdigest(),
                               payload_sha256=hashlib.sha256(payload).hexdigest(), output=str(output)))
    (probe_dir/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', default='build')
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--qt-dir', default=os.environ.get('MOONLIGHT_QT_DIR', str(ROOT.parent/'moonlight-qt')))
    parser.add_argument('--fixtures-dir', default='fixtures/generated')
    parser.add_argument('--output', default='results/reconfiguration.json')
    args = parser.parse_args()
    output = (ROOT/args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    # Replace any old successful result before attempting extraction or build.
    record = dict(schema_version=1, status='RUNNING', test='real-vt-reconfiguration')
    output.write_text(json.dumps(record, indent=2)+'\n')
    try:
        if platform.system() != 'Darwin':
            raise RuntimeError('physical Apple VideoToolbox hardware is required')
        probes = ROOT/'build/probes'
        provenance = extract_probes(pathlib.Path(args.qt_dir).expanduser().resolve(), probes)
        build = (ROOT/args.build_dir).resolve()
        fixtures = (ROOT/args.fixtures_dir).resolve()
        if not args.skip_build:
            cmake = os.environ.get('CMAKE', 'cmake')
            command([cmake, '-S', ROOT, '-B', build, '-DCMAKE_BUILD_TYPE=Release', '-DMAV_BUILD_TOOLS=ON'])
            command([cmake, '--build', build, '--target', 'mav-reconfiguration', '--parallel', '4'])
        command([build/'mav-reconfiguration', probes, fixtures, output])
        record = json.loads(output.read_text())
        if record.get('status') != 'PASS':
            raise RuntimeError('native reconfiguration test did not report PASS')
        record.update(test='real-vt-reconfiguration', probe_extraction=provenance,
                      probe_source_checkout=str(pathlib.Path(args.qt_dir).expanduser().resolve()))
    except Exception as error:
        # Preserve the native test's more specific failure, when it wrote one.
        native = json.loads(output.read_text())
        record.update(status='FAIL', reason=str(error))
        if native.get('status') == 'FAIL':
            record['native_failure'] = native
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(f'{record["status"]}: {output}')
    return 0 if record['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
