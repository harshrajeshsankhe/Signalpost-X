#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from agent.high_recall import enrich_profile, merge_enrichment

def read(path): return [json.loads(x) for x in Path(path).read_text(encoding='utf-8').splitlines() if x.strip()]
def _json_safe(v):
    if isinstance(v,bytes): return v.decode("utf-8",errors="replace")
    if isinstance(v,dict): return {k:_json_safe(x) for k,x in v.items()}
    if isinstance(v,list): return [_json_safe(x) for x in v]
    return v

def write(path,rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(''.join(json.dumps(_json_safe(x),ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8'); tmp.replace(p)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',required=True); ap.add_argument('--output',required=True); ap.add_argument('--report',required=True); ap.add_argument('--workers',type=int,default=8); ap.add_argument('--max-pages',type=int,default=12); ap.add_argument('--timeout',type=float,default=10); ap.add_argument('--limit',type=int,default=1000); ap.add_argument('--snapshot-dir')
    a=ap.parse_args(); rows=read(a.input); rows=rows[:a.limit]; started=time.time(); results={}; requests=bytes_=0
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futs={pool.submit(enrich_profile,r,max_pages=a.max_pages,timeout=a.timeout,snapshot_dir=a.snapshot_dir):r['organisation_number'] for r in rows}
        for f in as_completed(futs):
            org=futs[f]
            try: results[org]=f.result()
            except Exception as e: results[org]={"organisation_number":org,"status":"failed","error":type(e).__name__+': '+str(e)[:160],"requests":0,"bytes":0}
    out=[]
    for r in rows:
        e=results[r['organisation_number']]; out.append(merge_enrichment(r,e)); requests+=int(e.get('requests',0) or 0); bytes_+=int(e.get('bytes',0) or 0)
    write(a.output,out)
    report={"profiles":len(out),"site_available":sum(1 for x in results.values() if x.get('status')=='available'),"site_ambiguous":sum(1 for x in results.values() if x.get('status')=='ambiguous'),"site_not_available":sum(1 for x in results.values() if x.get('status')=='not_available'),"failed":sum(1 for x in results.values() if x.get('status')=='failed'),"requests":requests,"bytes":bytes_,"elapsed_seconds":round(time.time()-started,2),"max_pages":a.max_pages,"workers":a.workers}
    Path(a.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
