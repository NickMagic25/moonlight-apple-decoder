#!/usr/bin/env python3
import argparse,json,os,pathlib,subprocess,sys,math
from validation import ROOT,build,fixture,run
from environment import capture
PRESETS={}
for size,w,h,rates in [('1080p',1920,1080,[60,120]),('1440p',2560,1440,[120,240]),('3440x1440p',3440,1440,[120,240]),('4k',3840,2160,[60,120])]:
    for fps in rates:
        for codec in ['av1','hevc']:
            PRESETS[f'{size}{fps}-{codec}']=(w,h,fps,codec,'sdr8')
            suffix='10bit-hdr' if codec=='av1' else 'main10-hdr'
            PRESETS[f'{size}{fps}-{codec}-{suffix}']=(w,h,fps,codec,'hdr10')
def main():
    p=argparse.ArgumentParser();p.add_argument('--preset',choices=sorted(PRESETS),required=True);p.add_argument('--results-dir',default='results/benchmarks');p.add_argument('--inflight',default='2');p.add_argument('--queue-depth',type=int,default=16);p.add_argument('--repetitions',type=int,default=3);p.add_argument('--seconds',type=int,default=10);p.add_argument('--warmup',type=int,default=120);p.add_argument('--power',choices=['-1','0'],default='-1');p.add_argument('--build-dir',default='build');p.add_argument('--skip-build',action='store_true');p.add_argument('--ffmpeg-baseline',action='store_true');p.add_argument('--chroma',default='420',choices=['420','444']);a=p.parse_args()
    out=ROOT/a.results_dir/a.preset;out.mkdir(parents=True,exist_ok=True);results=[]
    try:
        if a.chroma=='444':raise RuntimeError('BLOCKED: native library and adapter currently implement 4:2:0 only; 4:4:4 hardware support is not measured')
        inflights=[int(x) for x in a.inflight.split(',')]
        if not 1<=a.queue_depth<=4096:p.error('queue-depth must be 1..4096')
        if any(x not in [1,2,3] for x in inflights) or not 1<=a.repetitions<=20 or not 1<=a.seconds<=600:p.error('inflight1/2/3, repetitions1..20, seconds1..600 required')
        directory=(ROOT/a.build_dir).resolve()
        if not a.skip_build:build(directory)
        environment=capture(ROOT,directory,out/'environment.json')
        if environment['build_type']!='Release':raise RuntimeError('benchmark requires a Release build')
        w,h,fps,codec,variant=PRESETS[a.preset]
        manifest=fixture(directory,codec,variant,frames=max(120,fps),width=w,height=h,fps=fps)
        # Mandatory independent correctness gate before timed sinks. Never benchmark malformed or mislabelled fixture.
        gate=run([directory/'mav-replay','--fixture',manifest,'--mode','correctness','--output',out/'correctness'])
        if gate.returncode:raise RuntimeError('hardware correctness gate failed for requested codec/variant/dimensions')
        units=len(json.loads(manifest.read_text())['access_units']);loopcount=max(1,math.ceil(a.seconds*fps/units))
        for inflight in inflights:
            for rep in range(a.repetitions):
                prefix=out/f'native-inflight{inflight}-power{a.power}-rep{rep+1}'
                r=run([directory/'mav-replay','--fixture',manifest,'--mode','paced','--fps',fps,'--loops',loopcount,'--loop-mode','continuous','--warmup',a.warmup,'--inflight',inflight,'--queue-depth',a.queue_depth,'--power',a.power,'--output',prefix],capture_output=True,text=True)
                print(r.stdout,end='');print(r.stderr,end='',file=sys.stderr)
                item=dict(backend='native',inflight=inflight,queue_depth=a.queue_depth,repetition=rep+1,status='PASS' if not r.returncode else 'FAIL',reason=r.stderr.strip(),result=str(prefix)+'.json');results.append(item)
        if a.ffmpeg_baseline:
            binary=directory/'mav-ffmpeg-baseline'
            if not binary.exists():results.append(dict(backend='ffmpeg-videotoolbox',status='BLOCKED',reason='optional baseline tool was not built with suitable FFmpeg'))
            else:
                baseline_env=os.environ.copy()
                cache=directory/'CMakeCache.txt'
                if cache.exists():
                    for line in cache.read_text().splitlines():
                        if line.startswith('MAV_FFMPEG_ROOT:PATH=') and line.split('=',1)[1]:
                            baseline_env['DYLD_LIBRARY_PATH']=line.split('=',1)[1]+'/lib'+(':'+baseline_env['DYLD_LIBRARY_PATH'] if baseline_env.get('DYLD_LIBRARY_PATH') else '')
                for rep in range(a.repetitions):
                    prefix=out/f'ffmpeg-rep{rep+1}'
                    r=run([binary,'--fixture',manifest,'--mode','paced','--fps',fps,'--loops',loopcount,'--loop-mode','continuous','--warmup',a.warmup,'--output',prefix],env=baseline_env)
                    results.append(dict(backend='ffmpeg-videotoolbox',repetition=rep+1,status='PASS' if not r.returncode else 'BLOCKED',result=str(prefix)+'.json'))

    except Exception as e:results.append(dict(status='BLOCKED',reason=str(e)))
    bad=any(x['status']!='PASS' for x in results);summary=dict(schema_version=1,preset=a.preset,status='FAIL' if bad else 'PASS',headless_only=True,native_scheduler_queue_depth=a.queue_depth,ffmpeg_scheduler_queue_policy='drains scheduled AUs without age-based dropping',results=results)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(bad)
if __name__=='__main__':sys.exit(main())
