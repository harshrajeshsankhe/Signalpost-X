#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, hashlib, json
from collections import defaultdict
from pathlib import Path

def band(e):
    if e is None: return 'missing'
    if e == 0: return '0'
    if e < 5: return '1-4'
    if e < 20: return '5-19'
    if e < 100: return '20-99'
    return '100+'

def row_key(r):
    return '|'.join([
        str(r.get('legal_form') or 'missing'), band(r.get('employees')),
        'adverse' if r.get('bankrupt') or r.get('liquidating') else 'active',
        'web' if r.get('website') else 'no-web',
        str(r.get('industry_code') or 'missing').split('.')[0],
        str(r.get('municipality_number') or 'missing')[:2]
    ])

def read(path):
    opener=gzip.open if str(path).endswith('.gz') else open
    with opener(path,'rt',encoding='utf-8-sig') as f:
        for line in f:
            if line.strip(): yield json.loads(line)

def rank(seed, org):
    return hashlib.sha256(f'{seed}:{org}'.encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--universe',required=True); ap.add_argument('--count',type=int,default=1000)
    ap.add_argument('--seed',type=int,default=20260913); ap.add_argument('--output',required=True)
    args=ap.parse_args()
    if args.count < 1000: raise SystemExit('Signalpost entry minimum is 1,000 profiles')
    buckets=defaultdict(list); total=0
    for r in read(args.universe):
        total += 1; buckets[row_key(r)].append(r)
    # First take one representative from every stratum, then allocate the remainder by
    # inverse stratum frequency. This prevents a huge AS/employee band from dominating.
    strata=sorted(buckets)
    chosen=[]; used=set()
    for s in strata:
        pool=buckets[s]
        item=min(pool,key=lambda r:rank(args.seed,r['organisation_number']))
        chosen.append(item); used.add(item['organisation_number'])
    remaining=args.count-len(chosen)
    if remaining < 0:
        chosen=sorted(chosen,key=lambda r:rank(args.seed+'-trim' if isinstance(args.seed,str) else str(args.seed)+'-trim',r['organisation_number']))[:args.count]
    else:
        candidates=[]
        for s,pool in buckets.items():
            weight=max(1, int((total/max(1,len(pool)))**0.5))
            for r in pool:
                if r['organisation_number'] in used: continue
                candidates.append((rank(args.seed+weight if isinstance(args.seed,str) else str(args.seed)+':'+str(weight),r['organisation_number']),r))
        candidates.sort(key=lambda x:x[0])
        chosen.extend(r for _,r in candidates[:remaining])
    chosen=chosen[:args.count]
    chosen.sort(key=lambda r:rank(str(args.seed)+':order',r['organisation_number']))
    dev=round(args.count*.6); val=round(args.count*.2)
    for i,r in enumerate(chosen):
        r=dict(r); r['sample_slice']='stratified'; r['evaluation_split']='development' if i<dev else 'validation' if i<dev+val else 'held_out'; chosen[i]=r
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8') as f:
        for r in chosen: f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    manifest='\n'.join(r['organisation_number'] for r in chosen)
    meta={
      'agent':'Signalpost X','seed':args.seed,'universe_rows':total,'selected':len(chosen),
      'strata':len(strata),'selected_sha256':hashlib.sha256(manifest.encode()).hexdigest(),
      'web_count':sum(bool(r.get('website')) for r in chosen),'no_web_count':sum(not r.get('website') for r in chosen),
      'legal_forms':{k:sum(r.get('legal_form')==k for r in chosen) for k in sorted({r.get('legal_form') for r in chosen})},
      'evaluation_splits':{'development':dev,'validation':min(val,max(0,len(chosen)-dev)),'held_out':max(0,len(chosen)-dev-val)}
    }
    Path(str(out)+'.meta.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(meta,indent=2,ensure_ascii=False))
if __name__=='__main__': main()
