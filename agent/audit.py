#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,collections
from pathlib import Path

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--profiles',required=True); ap.add_argument('--output',required=True); a=ap.parse_args()
 rows=[json.loads(x) for x in Path(a.profiles).read_text(encoding='utf-8').splitlines() if x.strip()]
 risks=[]; stats=collections.Counter()
 for r in rows:
  stats['companies']+=1
  for k,v in r.get('evidence',{}).items():
   if not isinstance(v,dict): continue
   stats[f'status:{v.get("status")}']+=1
   if v.get('status')=='available': stats['available_modules']+=1
   val=v.get('value') or {}
   assess=(val.get('identity_assessment') if isinstance(val,dict) else None) or {}
   if assess and not assess.get('publishable',False): risks.append({'organisation_number':r.get('organisation_number'),'module':k,'risk':'identity_quarantined','score':assess.get('score')})
  if not r.get('name'): risks.append({'organisation_number':r.get('organisation_number'),'risk':'missing_name'})
 out={'stats':dict(stats),'risk_count':len(risks),'risks':risks[:500]}
 Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'companies':len(rows),'risk_count':len(risks)},indent=2))
if __name__=='__main__': main()
