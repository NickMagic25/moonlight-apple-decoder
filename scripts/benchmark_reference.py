"""Bounded, independently decoded references for lossy noise fixtures.

The runner must pass the generated raw reference to native correctness mode and
require the complete sample count. Changing a pattern label alone is not a
correctness check. Raw references may be deleted after successful comparisons;
the archived helper metadata, commands, sizes, and hashes remain verifiable.
"""

import hashlib
import json
import math
import os
import pathlib
import re


SOURCE_PATTERN = 'moving-gradient-detail-square-frame-id-v1'
REFERENCE_PATTERN = 'seeded-noise-software-reference-v1'
SOFTWARE_DECODERS = {'av1': {'libdav1d', 'libaom-av1'}, 'hevc': {'hevc'}}


def requires_reference(generator):
    return isinstance(generator, dict) and (
        generator.get('content_profile') == 'seeded-noise-frame-id-v1'
        or generator.get('pattern') == REFERENCE_PATTERN)


def _sha(path):
    digest = hashlib.sha256()
    try:
        with path.open('rb') as source:
            for block in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(block)
    except OSError as error:
        raise ValueError('software reference: cannot hash artifact ' + str(path)) from error
    return digest.hexdigest()


def _hash(value, label):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('software reference: invalid ' + label + ' hash')
    return value


def _read_json(path, limit=64 * 1024):
    def invalid(value):
        raise ValueError('software reference: non-finite JSON number ' + value)
    try:
        if path.stat().st_size > limit:
            raise ValueError('software reference: oversized metadata ' + str(path))
        result = json.loads(path.read_text(), parse_constant=invalid)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('software reference: cannot read metadata ' + str(path)) from error
    if not isinstance(result, dict):
        raise ValueError('software reference: metadata must be a mapping')
    return result


def _relative(path, out):
    try:
        return str(path.resolve().relative_to(out.resolve()))
    except ValueError as error:
        raise ValueError('software reference: artifact escapes results directory') from error


def _artifact(out, value):
    if not isinstance(value, str) or not value or pathlib.Path(value).is_absolute():
        raise ValueError('software reference: artifact path must be relative')
    result = out / value
    _relative(result, out)
    return result


def _expected(case):
    for field in ('width', 'height', 'frames'):
        if type(case.get(field)) is not int or case[field] <= 0:
            raise ValueError('software reference: invalid case ' + field)
    if case['width'] % 2 or case['height'] % 2:
        raise ValueError('software reference: dimensions must be even for 4:2:0')
    if case.get('codec') not in SOFTWARE_DECODERS or case.get('dynamic_range') not in ('sdr', 'hdr10'):
        raise ValueError('software reference: unsupported codec or dynamic range')
    depth = 10 if case['dynamic_range'] == 'hdr10' else 8
    samples = case['width'] * case['height'] * 3 // 2 * case['frames']
    return dict(expected_samples=samples, expected_outputs=case['frames'],
                raw_bytes=samples * (2 if depth == 10 else 1), bit_depth=depth,
                packing='yuv420p10le-low-bits' if depth == 10 else 'yuv420p')


def _fixture(manifest, case):
    expected = _expected(case)
    document = _read_json(manifest, 64 * 1024 * 1024)
    if any(document.get(key) != case[key] for key in ('width', 'height', 'codec')):
        raise ValueError('software reference: fixture dimensions or codec differ from case')
    if document.get('bit_depth') != expected['bit_depth'] or document.get('chroma') != '420':
        raise ValueError('software reference: fixture pixel format differs from case')
    units = document.get('access_units')
    if (not isinstance(units, list) or len(units) != case['frames']
            or any(not isinstance(unit, dict) or type(unit.get('expected_display_count')) is not int
                   or unit['expected_display_count'] != 1 for unit in units)):
        raise ValueError('software reference: fixture must display exactly one frame per access unit')
    payload = _artifact(manifest.parent, document.get('payload_file'))
    payload_hash = _hash(document.get('payload_sha256'), 'fixture payload')
    if not payload.is_file() or _sha(payload) != payload_hash:
        raise ValueError('software reference: fixture payload hash mismatch')
    return dict(fixture_manifest_sha256=_sha(manifest), fixture_payload_sha256=payload_hash)


def _metadata(metadata, case, info):
    expected = _expected(case)
    if (metadata.get('status') != 'PASS' or metadata.get('codec') != case['codec']
            or type(metadata.get('outputs')) is not int or metadata['outputs'] != expected['expected_outputs']
            or metadata.get('packing') != expected['packing']
            or metadata.get('row_padding') != 'omitted'
            or metadata.get('fixture_sha256') != info['fixture_payload_sha256']
            or metadata.get('decoder') not in SOFTWARE_DECODERS[case['codec']]
            or not isinstance(metadata.get('ffmpeg_version'), str) or not metadata['ffmpeg_version']):
        raise ValueError('software reference: helper metadata does not prove the requested software decode')


def _loader_environment(tool):
    """Use an explicit loader path, or the helper's recorded FFmpeg build root.

    Do not change the process-wide environment or inspect unrelated user paths.
    The /usr/bin/env prefix is an argument vector passed through run_encoder's
    process-group timeout; no shell or additional subprocess is involved.
    """
    value = os.environ.get('DYLD_LIBRARY_PATH')
    if not value:
        cache = tool.parent / 'CMakeCache.txt'
        if cache.is_file():
            for line in cache.read_text().splitlines():
                if line.startswith('MAV_FFMPEG_ROOT:PATH='):
                    directory = pathlib.Path(line.split('=', 1)[1]) / 'lib'
                    if directory.is_dir():
                        value = str(directory.resolve())
                    break
    environment = {'DYLD_LIBRARY_PATH': value} if value else {}
    libraries = {}
    for directory in (value or '').split(':'):
        if not directory:
            continue
        base = pathlib.Path(directory)
        for pattern in ('libavcodec.*.dylib', 'libavutil.*.dylib', 'libdav1d*.dylib'):
            for library in sorted(base.glob(pattern)):
                if library.is_file():
                    libraries[str(library.resolve())] = _sha(library)
    return environment, libraries


def prepare_reference(tool, manifest, case, out, timeout, run_encoder):
    """Create and validate an independent raw reference using a bounded helper."""
    tool, manifest, out = pathlib.Path(tool).resolve(), pathlib.Path(manifest).resolve(), pathlib.Path(out).resolve()
    if not tool.is_file() or not os.access(tool, os.X_OK):
        raise ValueError('software reference: executable mav-reference-decode is missing; build it with MAV_FFMPEG_ROOT')
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('software reference: timeout must be finite and positive')
    name = case.get('name')
    if not isinstance(name, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*', name):
        raise ValueError('software reference: unsafe case name')
    expected = _expected(case)
    identity = _fixture(manifest, case)
    directory = out / 'reference'
    directory.mkdir(parents=True, exist_ok=True)
    raw = _artifact(out, 'reference/' + name + '.yuv')
    metadata_path = _artifact(out, 'reference/' + name + '.yuv.json')
    log_path = _artifact(out, 'reference/' + name + '.log')
    command_path = _artifact(out, 'reference/' + name + '-command.json')
    if raw.exists() or metadata_path.exists():
        raise ValueError('software reference: output already exists; use a fresh results directory')
    environment, libraries = _loader_environment(tool)
    command = [str(tool), '--fixture', str(manifest), '--output', str(raw)]
    if environment:
        command = ['/usr/bin/env', 'DYLD_LIBRARY_PATH=' + environment['DYLD_LIBRARY_PATH']] + command
    info = dict(status='PASS', raw_path=_relative(raw, out), metadata_path=_relative(metadata_path, out),
                log_path=_relative(log_path, out), command_path=_relative(command_path, out),
                fixture_manifest_path=_relative(manifest, out), tool_path=str(tool), tool_sha256=_sha(tool),
                command=command, environment=environment, libraries_sha256=libraries, **expected, **identity)
    # Record the attempt before execution, including failures and timeouts.
    command_path.write_text(json.dumps({key: info[key] for key in ('command', 'environment', 'tool_path',
        'tool_sha256', 'libraries_sha256', 'fixture_manifest_sha256', 'fixture_payload_sha256')}, indent=2) + '\n')
    info['command_sha256'] = _sha(command_path)
    try:
        with log_path.open('w') as log:
            result = run_encoder(command, log, timeout=timeout)
        if result.returncode:
            raise ValueError('software reference: helper failed (exit {}); see {}'.format(result.returncode, log_path))
        if not raw.is_file() or raw.stat().st_size != expected['raw_bytes']:
            raise ValueError('software reference: raw output size differs from complete expected frame count')
        metadata = _read_json(metadata_path)
        _metadata(metadata, case, info)
        info.update(raw_sha256=_sha(raw), metadata=metadata, metadata_sha256=_sha(metadata_path))
        validate_reference(info, case, out, require_raw=True)
        return info
    except BaseException:
        # Keep the command, logs and sidecar as failure evidence, but never
        # permit a partial or unvalidated raw file to reach native correctness.
        raw.unlink(missing_ok=True)
        raise


def validate_reference(info, case, out, require_raw=False):
    """Verify archived provenance, and optionally the raw bytes before replay."""
    out = pathlib.Path(out).resolve()
    if not isinstance(info, dict) or info.get('status') != 'PASS':
        raise ValueError('software reference: missing successful reference provenance')
    for field in ('raw_sha256', 'metadata_sha256', 'tool_sha256', 'command_sha256',
                  'fixture_manifest_sha256', 'fixture_payload_sha256'):
        _hash(info.get(field), field)
    for field, value in _expected(case).items():
        if info.get(field) != value or type(info.get(field)) is not type(value):
            raise ValueError('software reference: expected sample count, format or raw size changed')
    metadata_path = _artifact(out, info.get('metadata_path'))
    if _sha(metadata_path) != info['metadata_sha256']:
        raise ValueError('software reference: archived metadata hash mismatch')
    metadata = _read_json(metadata_path)
    if metadata != info.get('metadata'):
        raise ValueError('software reference: archived metadata differs from recorded metadata')
    _metadata(metadata, case, info)
    manifest = _artifact(out, info.get('fixture_manifest_path'))
    if _fixture(manifest, case) != {key: info[key] for key in ('fixture_manifest_sha256', 'fixture_payload_sha256')}:
        raise ValueError('software reference: archived fixture identity changed')
    command_path = _artifact(out, info.get('command_path'))
    if _sha(command_path) != info['command_sha256']:
        raise ValueError('software reference: archived command hash mismatch')
    recorded = _read_json(command_path)
    if recorded != {key: info.get(key) for key in ('command', 'environment', 'tool_path', 'tool_sha256',
                                                  'libraries_sha256', 'fixture_manifest_sha256', 'fixture_payload_sha256')}:
        raise ValueError('software reference: command provenance changed')
    for value in info.get('libraries_sha256', {}).values():
        _hash(value, 'software library')
    raw = _artifact(out, info.get('raw_path'))
    if require_raw and (not raw.is_file() or raw.stat().st_size != info['raw_bytes'] or _sha(raw) != info['raw_sha256']):
        raise ValueError('software reference: raw bytes missing or hash/size mismatch')
    return info


def cleanup_reference(info, out):
    """Remove only this generated raw file; retain its archived hashes/evidence."""
    out = pathlib.Path(out).resolve()
    raw = _artifact(out, info.get('raw_path'))
    if raw.parent.resolve() != (out / 'reference').resolve() or raw.suffix != '.yuv':
        raise ValueError('software reference: refusing to clean up an unrelated artifact')
    raw.unlink(missing_ok=True)
