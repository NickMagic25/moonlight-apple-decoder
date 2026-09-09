#!/usr/bin/env python3
"""Strict codec/variant accounting; no missing hardware or codec is a PASS."""
import argparse,json,os,pathlib,platform,subprocess,sys,time
from environment import capture
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(command,**kw):
    print('+',' '.join(map(str,command)),flush=True)
    return subprocess.run(list(map(str,command)),cwd=ROOT,**kw)
def build(directory):
    cmake=os.environ.get('CMAKE','cmake')
    for command in ([cmake,'-S',ROOT,'-B',directory,'-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=ON','-DMAV_BUILD_TOOLS=ON'],[cmake,'--build',directory,'--parallel',os.environ.get('JOBS','4')]):
        if run(command).returncode:raise RuntimeError('build failed; set CMAKE to an available CMake executable')
def fixture(directory,codec,variant,frames=120,width=1920,height=1080,fps=120,regenerate=False):
    target=ROOT/'fixtures/generated'/f'{codec}-{variant}-{width}x{height}p{fps}-{frames}'
    manifest=target/'manifest.json'
    if manifest.exists() and not regenerate:return manifest
    encoder=os.environ.get('AOMENC',str(ROOT/'.local/aom-build/aomenc'))
    if codec=='av1' and not pathlib.Path(encoder).is_file():
        raise RuntimeError('AV1 encoder missing: run ./scripts/bootstrap-aom.sh or set AOMENC; this is a fixture dependency only')
    command=[directory/'mav-fixture','--codec',codec,'--variant',variant,'--output',target,'--width',width,'--height',height,'--fps',fps,'--frames',frames,'--gop',min(60,frames),'--aomenc',encoder]
    result=run(command,capture_output=True,text=True)
    print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
    if result.returncode:raise RuntimeError(result.stderr.strip() or 'fixture generation failed')
    return manifest
def main():
    p=argparse.ArgumentParser();p.add_argument('--suite',choices=['correctness','offline-hardware'],default='correctness');p.add_argument('--require-hardware',action='store_true');p.add_argument('--require-codecs',default='');p.add_argument('--require-variants',default='');p.add_argument('--build-dir',default='build');p.add_argument('--regenerate',action='store_true');p.add_argument('--skip-build',action='store_true');a=p.parse_args()
    codecs=a.require_codecs.split(',') if a.require_codecs else ['av1','hevc'];variants=a.require_variants.split(',') if a.require_variants else ['sdr8','hdr10']
    if any(c not in ['av1','hevc'] for c in codecs) or any(v not in ['sdr8','hdr10'] for v in variants):p.error('codecs: av1,hevc; variants: sdr8,hdr10')
    directory=(ROOT/a.build_dir).resolve();results=[];out=ROOT/'results/validation';out.mkdir(parents=True,exist_ok=True)
    try:
        if not a.skip_build:build(directory)
        capture(ROOT,directory,out/'environment.json')
        if a.suite=='correctness':
            cmake=os.environ.get('CMAKE','cmake');ctest=str(pathlib.Path(cmake).with_name('ctest')) if '/' in cmake else 'ctest'
            code=run([ctest,'--test-dir',directory,'--output-on-failure']).returncode
            results.append(dict(test='portable-parser-lifecycle-c-abi',status='PASS' if code==0 else 'FAIL',reason='CTest exit '+str(code)))
        if platform.system()!='Darwin':
            for codec in codecs:
                for variant in variants:results.append(dict(codec=codec,variant=variant,status='BLOCKED',reason='physical Apple VideoToolbox hardware unavailable'))
        else:
            for codec in codecs:
                for variant in variants:
                    item=dict(codec=codec,variant=variant)
                    try:
                        manifest=fixture(directory,codec,variant,regenerate=a.regenerate)
                        prefix=out/f'{codec}-{variant}'
                        command=[directory/'mav-replay','--fixture',manifest,'--mode','correctness','--loops','2','--output',prefix]
                        r=run(command,capture_output=True,text=True);print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr)
                        item.update(status='PASS' if r.returncode==0 else 'FAIL',reason=r.stderr.strip() if r.returncode else 'real hardware, metadata, IOSurface/Metal, visible frame ID, reset and retained ownership',result=str(prefix)+'.json')
                    except Exception as e:item.update(status='BLOCKED',reason=str(e))
                    results.append(item)
    except Exception as e:results.append(dict(test='build',status='BLOCKED',reason=str(e)))
    strict=bool(a.require_hardware or a.require_codecs or a.require_variants or a.suite=='offline-hardware')
    bad=any(r['status']=='FAIL' or (strict and r['status']!='PASS') for r in results)
    # Default correctness can disclose hardware blockers while portable tests pass.
    if not any(r['status']=='PASS' for r in results):bad=True
    document=dict(schema_version=1,suite=a.suite,strict=strict,status='FAIL' if bad else ('PASS' if all(r['status']=='PASS' for r in results) else 'PARTIAL'),results=results)
    (out/'summary.json').write_text(json.dumps(document,indent=2)+'\n');print(json.dumps(document,indent=2));return int(bad)
if __name__=='__main__':sys.exit(main())
