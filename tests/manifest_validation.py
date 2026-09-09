#!/usr/bin/env python3
"""Exercise malformed fixture metadata through the real native importer (no VT)."""
import argparse,copy,json,pathlib,shutil,subprocess,tempfile,sys
p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--tool',default='build/mav-fixture');a=p.parse_args()
source=pathlib.Path(a.fixture).resolve();tool=pathlib.Path(a.tool).resolve();original=json.loads(source.read_text())
cases=[('codec-type',lambda d:d.update(codec=[])),('rate-type',lambda d:d.update(frame_rate=[])),('timebase-type',lambda d:d.update(timebase='bad')),('generator-type',lambda d:d.update(generator=[])),('pattern-type',lambda d:d.update(generator={'pattern':[]})),('color-type',lambda d:d.update(color=[])),('color-value-type',lambda d:d.update(color={'primaries':[]})),('odd-width',lambda d:d.update(width=1919)),('chroma-mismatch',lambda d:d.update(chroma='444')),('profile-mismatch',lambda d:d.update(profile=2 if d['codec']=='av1' else 0)),('pts-type',lambda d:d['access_units'][0].update(pts=[])),('dts-type',lambda d:d['access_units'][0].update(dts={})),('bool-type',lambda d:d['access_units'][0].update(random_access=[])),('discontinuity-type',lambda d:d['access_units'][0].update(discontinuity='true')),('negative-offset',lambda d:d['access_units'][0].update(offset=-1)),('oversized-length',lambda d:d['access_units'][0].update(length=1<<31)),('display-count',lambda d:d['access_units'][0].update(expected_display_count=2)),('unit-type',lambda d:d['access_units'].__setitem__(0,[])),('payload-hash',lambda d:d.update(payload_sha256='0'*64)),('traversal',lambda d:d.update(payload_file='../payload.bin')),('duplicate-id',lambda d:d['access_units'][1].update(frame_id=d['access_units'][0]['frame_id']))]
with tempfile.TemporaryDirectory(prefix='mav-manifest-') as temporary:
 root=pathlib.Path(temporary);shutil.copyfile(source.parent/original['payload_file'],root/'payload.bin')
 original['payload_file']='payload.bin';manifest=root/'manifest.json';manifest.write_text(json.dumps(original));out=root/'imported'
 def check():return subprocess.run([str(tool),'--import',str(manifest),'--output',str(out)],capture_output=True,text=True)
 positive=check()
 if positive.returncode:print('FAIL valid fixture:',positive.stderr);sys.exit(1)
 for name,mutate in cases:
  document=copy.deepcopy(original);mutate(document);manifest.write_text(json.dumps(document));result=check()
  if result.returncode!=1 or 'BLOCKED/FAIL:' not in result.stderr:print('FAIL malformed case',name,'exit',result.returncode,result.stderr);sys.exit(1)
 print('PASS manifest importer: valid baseline plus',len(cases),'malformed structure/bounds/hash/type cases')
