#!/usr/bin/env python3
"""High-recall enrichment with canonical publication and evidence snapshots."""
from __future__ import annotations
import hashlib, json, os, re, time
from pathlib import Path
from typing import Any
from .site_intelligence import crawl
from .winning_model import choose_routes
from .canonical_claims import promote_external_claims
from norway_company_agent.website import normalize_social_url

NORWEGIAN_PATH_HINTS = {
    "people": ("ansatte", "team", "ledelse", "styre", "om-oss", "people", "management"),
    "jobs": ("jobb", "jobber", "karriere", "career", "ledige-stillinger", "vacancies", "stillinger"),
    "activity": ("nyhet", "nyheter", "news", "aktuelt", "prosjekt", "referanser", "case", "blog"),
}

def _pick_links(pages: list[dict], hints: tuple[str, ...], limit: int = 8) -> list[str]:
    out=[]
    for page in pages:
        for m in re.finditer(r'https?://[^\s<>"\']+', page.get("text", "")):
            u=m.group(0).rstrip(').,;')
            if any(h in u.casefold() for h in hints) and u not in out: out.append(u)
    return out[:limit]

def _extract_emails(text: str) -> list[str]:
    return sorted(set(re.findall(r"[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+", text, re.I)))[:20]

def _extract_socials(text: str) -> list[str]:
    urls=re.findall(r'https?://[^\s<>"\']+', text)
    domains=("linkedin.com/", "facebook.com/", "instagram.com/", "youtube.com/", "x.com/", "twitter.com/", "tiktok.com/")
    return sorted(set(u.rstrip(').,;') for u in urls if any(d in u.casefold() for d in domains)))[:20]

def enrich_profile(profile: dict, *, max_pages: int = 12, timeout: float = 10.0, snapshot_dir: str | None = None) -> dict:
    website=str(profile.get("website") or "").strip()
    result={"organisation_number":str(profile.get("organisation_number")),"source":"company_site","status":"not_available","requests":0,"bytes":0,"identity":"not_checked","facts":{},"pages":[],"strategy":choose_routes(requests_used=0, remaining_cost=10.0, has_verified_site=bool(website), missing_fields=("people","jobs","activity","contact"))}
    if not website:
        result["note"]="No registry website supplied; use optional discovery stage."
        return result
    site=crawl(profile,max_pages=max_pages,timeout=timeout,snapshot_dir=snapshot_dir)
    result.update({k:site.get(k) for k in ("status","requests","bytes","identity","identity_score") if k in site})
    result["pages"]=[{k:p.get(k) for k in ("url","title","text","retrieved_at","content_sha256","snapshot_path") if k in p} for p in site.get("pages",[])]
    if site.get("identity")!="exact":
        result["status"]="ambiguous"; result["note"]="Website crawled but exact-entity gate did not pass; no external facts promoted."; return result
    texts=[p.get("text","") for p in site.get("pages",[])]
    joined="\n".join(texts)
    first=site.get("pages",[])[0] if site.get("pages") else {}

    email_items=[]
    social_items=[]

    for page in site.get("pages",[]):
        page_text=page.get("text","")
        for email in _extract_emails(page_text):
            email_items.append({
                "value": email,
                "source": page,
                "claim_span": email,
            })

        for raw_url in _extract_socials(page_text):
            normalized=normalize_social_url(raw_url)
            if normalized:
                social_items.append({
                    "platform": normalized.get("platform"),
                    "url": normalized.get("url"),
                    "source": page,
                    "claim_span": raw_url,
                })

    result["facts"]={
        "contact_emails":{
            "value":sorted(set(x["value"] for x in email_items)),
            "items":email_items,
            "source_url":first.get("url"),
        },
        "social_links":{
            "value":[
                {"platform":x["platform"],"url":x["url"]}
                for x in social_items
            ],
            "items":social_items,
            "source_url":first.get("url"),
        },
        "people_pages":{
            "value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["people"]),
            "source_url":first.get("url"),
        },
        "job_pages":{
            "value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["jobs"]),
            "source_url":first.get("url"),
        },
        "activity_pages":{
            "value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["activity"]),
            "source_url":first.get("url"),
        },
    }
    result["status"]="available"
    result["content_sha256"]=hashlib.sha256("\n".join(sorted(p.get("content_sha256","") for p in site.get("pages",[]))).encode()).hexdigest()
    return result

def merge_enrichment(profile: dict, enrichment: dict, *, snapshot_dir: str | None = None) -> dict:
    evidence=profile.setdefault("evidence",{})
    pages=enrichment.get("pages") or []
    snapshots=[{"url":p.get("url"),"content_sha256":p.get("content_sha256"),"retrieved_at":p.get("retrieved_at"),"snapshot_path":p.get("snapshot_path")} for p in pages if p.get("snapshot_path")]
    evidence["external_site_intelligence"]={"status":enrichment.get("status"),"source_type":"company_site","source_url":pages[0].get("url") if pages else None,"retrieved_at":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),"value":enrichment,"content_sha256":enrichment.get("content_sha256"),"snapshots":snapshots}
    return promote_external_claims(profile,enrichment,snapshot_dir=snapshot_dir)
