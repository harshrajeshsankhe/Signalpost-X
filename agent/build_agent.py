#!/usr/bin/env python3
"""Single-command Signalpost X runner.

This wraps the Builderr starter batch, optionally performs missing-website discovery,
and emits an audit manifest. It intentionally preserves the starter's terminal envelope.
"""
from __future__ import annotations
import argparse,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run(cmd):
    print('+',' '.join(map(str,cmd)),flush=True); return subprocess.run(cmd,check=True).returncode

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--organisations',required=True); ap.add_argument('--bulk',required=True); ap.add_argument('--out',default='out'); ap.add_argument('--run-id',default='signalpost-x'); ap.add_argument('--expected-count',type=int,default=100); ap.add_argument('--workers',type=int,default=8); ap.add_argument('--with-brave',action='store_true'); ap.add_argument('--brave-limit',type=int,default=100); ap.add_argument('--high-recall',action='store_true'); ap.add_argument('--site-pages',type=int,default=12)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    profiles=out/'profiles.jsonl'; envelopes=out/'envelopes.jsonl'; report=out/'run-report.json'
    cmd=[sys.executable,str(ROOT/'scripts/run_competition_batch.py'),'--organisations',a.organisations,'--bulk',a.bulk,'--profiles-output',profiles,'--output',envelopes,'--report',report,'--run-id',a.run_id,'--expected-count',str(a.expected_count),'--workers',str(a.workers),'--checkpoint-every','25','--resume']
    run(cmd)
    if a.with_brave:
        if not os.environ.get('BRAVE_SEARCH_API_KEY'): raise SystemExit('BRAVE_SEARCH_API_KEY is required for --with-brave')
        run([sys.executable,str(ROOT/'scripts/run_brave_discovery.py'),'--input',profiles,'--output',out/'profiles-discovered.jsonl','--report',out/'discovery-report.json','--limit',str(a.brave_limit),'--promote-verified'])
    enriched=None
    if a.high_recall:
        enriched=out/'profiles-high-recall.jsonl'
        run([sys.executable,str(ROOT/'scripts/run_high_recall.py'),'--input',profiles,'--output',enriched,'--report',out/'high-recall-report.json','--limit',str(a.expected_count),'--max-pages',str(a.site_pages),'--workers',str(a.workers)])
    print(json.dumps({'status':'completed','profiles':str(profiles),'enriched_profiles':str(enriched) if enriched else None,'envelopes':str(envelopes),'report':str(report),'brave_enabled':a.with_brave,'high_recall_enabled':a.high_recall},indent=2))
if __name__=='__main__': main()
