#!/usr/bin/env python3
"""Validate and package a Signalpost final submission without inventing results."""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def rows(path): return [json.loads(x) for x in Path(path).read_text(encoding='utf8').splitlines() if x.strip()]

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--profiles',required=True); ap.add_argument('--manifest',required=True); ap.add_argument('--envelopes'); ap.add_argument('--output',default='out/final-submission-manifest.json'); a=ap.parse_args()
 profiles=rows(a.profiles); manifest=rows(a.manifest); orgs=[str(x['organisation_number']) for x in manifest]
 p_orgs=[str(x.get('organisation_number')) for x in profiles]
 errors=[]
 if len(manifest)<1000: errors.append(f'manifest has {len(manifest)} rows; need >=1000')
 if len(profiles)<1000: errors.append(f'profiles has {len(profiles)} rows; need >=1000 completed profiles')
 if len(set(orgs))!=len(orgs): errors.append('manifest contains duplicate organisation numbers')
 if len(set(p_orgs))!=len(p_orgs): errors.append('profiles contain duplicate organisation numbers')
 if set(orgs)!=set(p_orgs): errors.append('profile organisation numbers do not exactly match manifest')
 for i,p in enumerate(profiles):
  if not p.get('organisation_number') or not p.get('name'): errors.append(f'profile {i} missing identity')
  if not isinstance(p.get('evidence'),dict): errors.append(f'profile {p.get("organisation_number")} missing evidence object')
 if a.envelopes:
  env=rows(a.envelopes)
  if len(env)!=100: errors.append(f'envelopes has {len(env)}; daily run requires exactly 100')
  allowed={'available','not_available','blocked','not_applicable','ambiguous','failed'}
  for e in env:
   if e.get('availability') not in allowed and e.get('state') not in allowed: errors.append('envelope contains invalid availability state')
 commit='unknown'
 try: commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[1],text=True).strip()
 except Exception: pass
 out={'ready':not errors,'errors':errors,'profile_count':len(profiles),'manifest_count':len(manifest),'manifest_sha256':sha(a.manifest),'profiles_sha256':sha(a.profiles),'git_commit':commit}
 if a.envelopes: out['envelopes_sha256']=sha(a.envelopes)
 Path(a.output).parent.mkdir(parents=True,exist_ok=True); Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8'); print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(0 if not errors else 2)
if __name__=='__main__': main()
