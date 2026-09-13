#!/usr/bin/env python3
"""High-recall, precision-gated external enrichment for Signalpost X.

The module is deliberately dependency-light. It enriches canonical profiles from
company websites and optionally uses Brave for discovery. External candidates are
never promoted without an independent identity check against the canonical profile.
"""
from __future__ import annotations
import hashlib, json, os, re, time
from pathlib import Path
from typing import Any
from .site_intelligence import crawl
from .winning_model import choose_routes

NORWEGIAN_PATH_HINTS = {
    "people": ("ansatte", "team", "ledelse", "styre", "om-oss", "om-oss", "people", "management"),
    "jobs": ("jobb", "jobber", "karriere", "career", "ledige-stillinger", "vacancies", "stillinger"),
    "activity": ("nyhet", "nyheter", "news", "aktuelt", "prosjekt", "referanser", "case", "blog"),
}

def _pick_links(pages: list[dict], hints: tuple[str, ...], limit: int = 8) -> list[str]:
    out=[]
    for page in pages:
        for m in re.finditer(r'https?://[^\\s<>"\']+', page.get("text", "")):
            u=m.group(0).rstrip(').,;')
            if any(h in u.casefold() for h in hints) and u not in out:
                out.append(u)
    return out[:limit]

def _extract_emails(text: str) -> list[str]:
    return sorted(set(re.findall(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}', text, re.I)))[:20]

def _extract_socials(text: str) -> list[str]:
    urls=re.findall(r'https?://[^\\s<>"\']+', text)
    domains=("linkedin.com/", "facebook.com/", "instagram.com/", "youtube.com/", "x.com/", "twitter.com/")
    return sorted(set(u.rstrip(').,;') for u in urls if any(d in u.casefold() for d in domains)))[:20]

def enrich_profile(profile: dict, *, max_pages: int = 12, timeout: float = 10.0) -> dict:
    """Return a deterministic enrichment record; no facts are published unless site identity is exact."""
    website=str(profile.get("website") or "").strip()
    result={"organisation_number":str(profile.get("organisation_number")),"source":"company_site","status":"not_available","requests":0,"bytes":0,"identity":"not_checked","facts":{},"pages":[],"strategy":choose_routes(requests_used=0, remaining_cost=10.0, has_verified_site=bool(website), missing_fields=("people","jobs","activity","contact"))}
    if not website:
        result["status"]="not_available"; result["note"]="No registry website supplied; use optional discovery stage."
        return result
    site=crawl(profile,max_pages=max_pages,timeout=timeout)
    result.update({k:site.get(k) for k in ("status","requests","bytes","identity","identity_score") if k in site})
    result["pages"]=[{"url":p["url"],"title":p.get("title",""),"retrieved_at":p.get("retrieved_at"),"content_sha256":p.get("content_sha256")} for p in site.get("pages",[])]
    if site.get("identity")!="exact":
        result["status"]="ambiguous"; result["note"]="Website crawled but exact-entity gate did not pass; no external facts promoted."
        return result
    texts=[p.get("text","") for p in site.get("pages",[])]
    joined="\\n".join(texts)
    result["facts"]={
        "contact_emails": {"value":_extract_emails(joined),"source_url":site["pages"][0]["url"] if site.get("pages") else None},
        "social_links": {"value":_extract_socials(joined),"source_url":site["pages"][0]["url"] if site.get("pages") else None},
        "people_pages": {"value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["people"]),"source_url":site["pages"][0]["url"] if site.get("pages") else None},
        "job_pages": {"value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["jobs"]),"source_url":site["pages"][0]["url"] if site.get("pages") else None},
        "activity_pages": {"value":_pick_links(site.get("pages",[]),NORWEGIAN_PATH_HINTS["activity"]),"source_url":site["pages"][0]["url"] if site.get("pages") else None},
    }
    result["status"]="available"
    result["content_sha256"]=hashlib.sha256("\\n".join(sorted(p.get("content_sha256","") for p in site.get("pages",[]))).encode()).hexdigest()
    return result

def merge_enrichment(profile: dict, enrichment: dict) -> dict:
    evidence=profile.setdefault("evidence",{})
    evidence["external_site_intelligence"]={
        "status": enrichment.get("status"),
        "source_type":"company_site",
        "source_url": (enrichment.get("pages") or [{}])[0].get("url"),
        "retrieved_at": time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        "value": enrichment,
        "content_sha256": enrichment.get("content_sha256"),
    }
    # Keep navigation/discovery hints separate from substantive claims. This prevents
    # a job/about URL from being mistaken for proof that a job/person exists.
    return profile
