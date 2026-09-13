"""Canonical publication layer for externally discovered company facts.

Only deterministic, validated facts are promoted. Every published claim points
to an evidence record backed by a content-addressed source snapshot.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

EMAIL_RE = re.compile(
    r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Z0-9]"
    r"(?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+$",
    re.I,
)

SOCIAL_PATHS = {
    "linkedin": lambda p: len(p) >= 2 and p[0].casefold() == "company"
    and p[1].strip() not in {"", "about"},
    "facebook": lambda p: len(p) >= 1 and p[0].casefold()
    not in {"share", "sharer", "plugins", "groups", "events", "privacy", "policy.php"},
    "instagram": lambda p: len(p) >= 1 and p[0].casefold()
    not in {"p", "reel", "reels", "stories", "explore"},
    "x": lambda p: len(p) == 1 and p[0].casefold()
    not in {"intent", "share", "home", "search", "i"},
    "twitter": lambda p: len(p) == 1 and p[0].casefold()
    not in {"intent", "share", "home", "search"},
    "youtube": lambda p: len(p) >= 1
    and (p[0].startswith("@") or p[0].casefold() in {"channel", "user", "c"}),
    "tiktok": lambda p: len(p) >= 1 and p[0].startswith("@"),
}


def valid_email(value: Any) -> bool:
    s = str(value or "")
    if s != s.strip() or any(c in s for c in "\r\n\t"):
        return False
    if len(s) > 254 or ".." in s or s.count("@") != 1:
        return False
    return bool(EMAIL_RE.fullmatch(s))


def valid_social_url(value: Any, expected_platform: str | None = None) -> bool:
    s = str(value or "").strip()
    if not s or any(c in s for c in "\r\n\t<>\"'"):
        return False

    try:
        p = urlparse(s)
    except ValueError:
        return False

    if p.scheme != "https" or not p.hostname or p.query or p.fragment:
        return False

    host = p.hostname.casefold().removeprefix("www.")
    platform = {
        "twitter.com": "twitter",
        "x.com": "x",
        "linkedin.com": "linkedin",
        "facebook.com": "facebook",
        "instagram.com": "instagram",
        "youtube.com": "youtube",
        "tiktok.com": "tiktok",
    }.get(host)

    if platform is None or (
        expected_platform and platform != expected_platform
    ):
        return False

    parts = [x for x in p.path.split("/") if x]
    return SOCIAL_PATHS[platform](parts)


def _snapshot_for_source(
    page: dict[str, Any],
    snapshot_dir: str | Path | None,
) -> dict[str, Any] | None:
    digest = str(page.get("content_sha256") or "")
    raw = page.get("_raw")
    existing = page.get("snapshot_path")

    if len(digest) != 64:
        return None

    if existing and Path(existing).exists():
        path = Path(existing)
    elif raw and snapshot_dir:
        root = Path(snapshot_dir)
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{digest}.html"
        if not path.exists():
            path.write_bytes(raw)
    else:
        return None

    return {
        "path": str(path),
        "content_sha256": digest,
        "retrievable": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def promote_external_claims(
    profile: dict[str, Any],
    enrichment: dict[str, Any],
    *,
    snapshot_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Promote only validated website-derived facts into profile.claims."""

    existing = [
        c
        for c in profile.get("claims", [])
        if not str(c.get("field", "")).startswith("external_")
    ]

    evidence_rows = list(profile.get("claim_evidence", []))
    claims = existing[:]

    pages = enrichment.get("pages") or []

    if enrichment.get("status") != "available" or not pages:
        profile["claims"] = claims
        profile["claim_evidence"] = evidence_rows
        return profile

    def add_claim(
        field: str,
        value: Any,
        source: dict[str, Any],
        source_class: str = "company_owned",
        confidence: float = 0.97,
        claim_span: str | None = None,
    ) -> None:
        snapshot = _snapshot_for_source(source, snapshot_dir)
        if not snapshot:
            return

        digest = str(source.get("content_sha256") or "")
        evidence_id = f"ev-{digest[:20]}"

        if not any(e.get("id") == evidence_id for e in evidence_rows):
            evidence_rows.append(
                {
                    "id": evidence_id,
                    "source_url": source.get("url"),
                    "source_class": source_class,
                    "retrieved_at": source.get("retrieved_at"),
                    "content_sha256": digest,
                    "snapshot_path": snapshot["path"],
                    "snapshot_sha256": digest,
                    "retrievable": True,
                    "claim_span": claim_span
                    or source.get("title")
                    or source.get("text", "")[:500],
                    "rights_status": "permitted_public_page",
                }
            )

        claims.append(
            {
                "id": f"claim-{digest[:12]}-{len(claims) + 1}",
                "field": field,
                "value": value,
                "availability": "available",
                "confidence": confidence,
                "evidence_ids": [evidence_id],
            }
        )

    facts = enrichment.get("facts") or {}

    email_fact=facts.get("contact_emails",{}) or {}; email_items=email_fact.get("items") or [{"value":e,"source":pages[0],"claim_span":e} for e in email_fact.get("value",[]) or []]
    for item in email_items:
        email=str(item.get("value") or ""); source=item.get("source") or {}; span=item.get("claim_span") or email
        if valid_email(email): add_claim("external_contact_email",email,source,confidence=0.995,claim_span=span)
    social_fact=facts.get("social_links",{}) or {}; social_items=social_fact.get("items") or [{"platform":x.get("platform"),"url":x.get("url"),"source":pages[0],"claim_span":x.get("url")} for x in social_fact.get("value",[]) or [] if isinstance(x,dict)]
    for item in social_items:
        platform=str(item.get("platform") or "").casefold(); url=str(item.get("url") or ""); source=item.get("source") or {}; span=item.get("claim_span") or url
        if platform and valid_social_url(url,platform): add_claim("external_social_profile",{"platform":platform,"url":url},source,confidence=0.99,claim_span=span)

    profile["claims"] = claims
    profile["claim_evidence"] = evidence_rows
    profile["claim_validation"] = {
        "external_claims": len(
            [
                c
                for c in claims
                if str(c.get("field", "")).startswith("external_")
            ]
        ),
        "all_external_claims_have_evidence": all(
            c.get("evidence_ids")
            for c in claims
            if str(c.get("field", "")).startswith("external_")
        ),
        "retrievable_snapshots": sum(
            1 for e in evidence_rows if e.get("retrievable")
        ),
    }

    return profile
