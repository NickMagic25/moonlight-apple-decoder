"""Collect provenance outside the timed decoder run; unavailable is JSON null."""
import datetime, hashlib, json, os, pathlib, platform, subprocess

def capture(root, build, output):
    def command(args):
        try:
            p = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=10)
            return p.stdout.strip() if p.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    sources = [root/'CMakeLists.txt', root/'Package.swift']
    for directory in ('src', 'include', 'tools'):
        sources.extend(p for p in (root/directory).rglob('*') if p.is_file())
    source_hash = hashlib.sha256()
    for path in sorted(sources):
        source_hash.update(str(path.relative_to(root)).encode()+b'\0'+path.read_bytes())
    cache = {}
    if (build/'CMakeCache.txt').exists():
        for line in (build/'CMakeCache.txt').read_text().splitlines():
            if '=' in line and not line.startswith(('#','//')):
                key, value = line.split('=', 1); cache[key.split(':')[0]] = value
    result = dict(schema_version=1, captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), os=platform.platform(), architecture=platform.machine(),
        model=command(['sysctl','-n','hw.model']), soc=command(['sysctl','-n','machdep.cpu.brand_string']),
        sdk=command(['xcrun','--sdk','macosx','--show-sdk-version']),
        compiler=command(['xcrun','clang++','--version']),
        revision=command(['git','rev-parse','HEAD']),
        worktree_status=command(['git','status','--porcelain']),
        source_sha256=source_hash.hexdigest(),
        binaries={name:digest(build/name) for name in ('mav-replay','mav-fixture','mav-ffmpeg-baseline')},
        build_type=cache.get('CMAKE_BUILD_TYPE'), deployment_target=cache.get('CMAKE_OSX_DEPLOYMENT_TARGET'),
        power=command(['pmset','-g','batt']), thermal=command(['pmset','-g','therm']),
        clock='CLOCK_UPTIME_RAW on Apple; media PTS separate',
        notes='Provenance captured outside timing; headless decode is not presentation throughput.')
    output.write_text(json.dumps(result, indent=2)+'\n')
    return result
