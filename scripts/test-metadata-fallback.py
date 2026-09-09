#!/usr/bin/env python3
"""Remove only static HDR metadata, then replay with the original manifest fallback.

Picture, sequence/SPS, profile and actual 10-bit signaling stay unchanged. The
native importer revalidates every complete AU before the public-API replay.
"""
import argparse,hashlib,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def leb(data,at,end):
 value=0
 for n in range(8):
  if at>=end:raise ValueError('truncated LEB128')
  byte=data[at];at+=1;value|=(byte&127)<<(n*7)
  if byte<128:return value,at
 raise ValueError('oversized LEB128')
def strip_av1(data):
 output=bytearray();at=0;removed=0
 while at<len(data):
  start=at;header=data[at];at+=1
  if header&0x80 or header&1:raise ValueError('invalid AV1 OBU header')
  if header&4:
   if at>=len(data):raise ValueError('truncated OBU extension')
   at+=1
  if header&2:size,at=leb(data,at,len(data))
  else:size=len(data)-at
  end=at+size
  if end>len(data):raise ValueError('truncated OBU')
  static=False
  if (header>>3)&15==5:
   kind,_=leb(data,at,end);static=kind in (1,2)
  if static:removed+=1
  else:output.extend(data[start:end])
  at=end
 return bytes(output),removed

def rbsp(escaped):
 out=bytearray();zeros=0;at=0
 while at<len(escaped):
  value=escaped[at]
  if zeros>=2 and value==3:
   if at+1>=len(escaped) or escaped[at+1]>3:raise ValueError('invalid HEVC escape')
   at+=1;zeros=0;continue
  out.append(value);zeros=zeros+1 if value==0 else 0;at+=1
 return bytes(out)
def escape(raw):
 out=bytearray();zeros=0
 for value in raw:
  if zeros>=2 and value<=3:out.append(3);zeros=0
  out.append(value);zeros=zeros+1 if value==0 else 0
 return bytes(out)
def strip_hevc(data):
 markers=list(re.finditer(b'\x00\x00(?:\x00)?\x01',data))
 if not markers or markers[0].start()!=0:raise ValueError('HEVC fixture is not canonical Annex-B')
 output=bytearray();removed=0
 for i,marker in enumerate(markers):
  end=markers[i+1].start() if i+1<len(markers) else len(data);nal=data[marker.end():end]
  if len(nal)<2:raise ValueError('short HEVC NAL')
  if (nal[0]>>1)&63 not in (39,40):output.extend(data[marker.start():end]);continue
  raw=rbsp(nal[2:]);at=0;kept=bytearray();local_removed=0
  while at<len(raw):
   if raw[at]==128 and not any(raw[at+1:]):break
   start=at;kind=0;size=0
   while at<len(raw) and raw[at]==255:kind+=255;at+=1
   if at>=len(raw):raise ValueError('truncated SEI type')
   kind+=raw[at];at+=1
   while at<len(raw) and raw[at]==255:size+=255;at+=1
   if at>=len(raw):raise ValueError('truncated SEI size')
   size+=raw[at];at+=1;at+=size
   if at>len(raw):raise ValueError('truncated SEI payload')
   if kind in (137,144):local_removed+=1
   else:kept.extend(raw[start:at])
  removed+=local_removed
  if not local_removed:output.extend(data[marker.start():end])
  elif kept:output.extend(b'\0\0\0\1'+nal[:2]+escape(kept+b'\x80'))
 return bytes(output),removed

def run(command):
 print('+',' '.join(map(str,command)),flush=True)
 result=subprocess.run(list(map(str,command)),cwd=ROOT,capture_output=True,text=True)
 print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
 if result.returncode:raise RuntimeError(result.stderr.strip() or 'native command failed')
def case(codec,source,build):
 document=json.loads(source.read_text());assert document['codec']==codec and document['bit_depth']==10 and document['variant']=='hdr10'
 color=document['color']
 if not color.get('mastering_valid') or not color.get('content_light_valid') or not color.get('mastering_base64') or not color.get('content_light_base64'):raise ValueError('fixture lacks original manifest HDR metadata bytes; regenerate it')
 original=(source.parent/document['payload_file']).read_bytes();payload=bytearray();removed=0
 for unit in document['access_units']:
  data=original[unit['offset']:unit['offset']+unit['length']]
  stripped,count=(strip_av1 if codec=='av1' else strip_hevc)(data)
  if not stripped:raise ValueError('stripping left an empty AU')
  removed+=count;unit.update(offset=len(payload),length=len(stripped),sha256=hashlib.sha256(stripped).hexdigest());payload.extend(stripped)
 if not removed:raise ValueError('no static HDR metadata was found; test would be vacuous')
 target=ROOT/'fixtures/generated'/('metadata-fallback-'+codec);target.mkdir(parents=True,exist_ok=True)
 document.update(payload_file='payload.bin',payload_sha256=hashlib.sha256(payload).hexdigest(),metadata_fallback_test=dict(source_sha256=hashlib.sha256(original).hexdigest(),removed_static_metadata_records=removed,sequence_and_picture_payloads='unchanged'))
 (target/'payload.bin').write_bytes(payload);(target/'manifest.json').write_text(json.dumps(document,indent=2)+'\n')
 # Codec parser independently verifies dimensions and actual bit-depth in every AU.
 run([build/'mav-fixture','--import',target/'manifest.json','--output',target/'verified'])
 output=ROOT/'results/metadata-fallback'/codec;output.parent.mkdir(parents=True,exist_ok=True)
 run([build/'mav-replay','--fixture',target/'verified/manifest.json','--mode','correctness','--output',output])
 result=json.loads(output.with_suffix('.json').read_text())
 if result['status']!='PASS' or result['bit_depth']!=10 or not result['hardware_validated'] or result['manifest_fallback_color_valid']&24!=24:raise ValueError('fallback/hardware/bit-depth proof missing')
 return dict(codec=codec,variant='hdr10',status='PASS',static_metadata_records_removed=removed,bitstream_10bit_verified=True,displayed_outputs=result['displayed_outputs'],hardware_validated=True,result=str(output.with_suffix('.json')))
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--build-dir',default='build')
 for codec in ['av1','hevc']:parser.add_argument('--'+codec+'-fixture',default='fixtures/generated/'+codec+'-hdr10-1920x1080p120-120/manifest.json')
 args=parser.parse_args();build=(ROOT/args.build_dir).resolve();results=[]
 for codec in ['av1','hevc']:
  try:results.append(case(codec,(ROOT/getattr(args,codec+'_fixture')).resolve(),build))
  except Exception as error:results.append(dict(codec=codec,variant='hdr10',status='FAIL',reason=str(error)))
 failed=any(result['status']!='PASS' for result in results);summary=dict(schema_version=1,status='FAIL' if failed else 'PASS',test='out-of-band-static-HDR-fallback',results=results)
 out=ROOT/'results/metadata-fallback';out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2));return int(failed)
if __name__=='__main__':sys.exit(main())
