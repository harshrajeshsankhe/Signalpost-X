"""Signalpost X Winning Model: budget-aware evidence-first research policy.

The model is intentionally hybrid: deterministic identity/evidence gates do the
publication decisions; optional LLM/API stages may only rank or summarize already
verified evidence. This avoids spending budget on low-value pages and prevents an
LLM from inventing company facts.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class Route:
    name: str
    cost: int
    expected_recall: float
    precision_floor: float
    enabled: bool = True

# Ordered by expected marginal evidence per request. Registry is handled by the
# starter runner; these are external discovery/enrichment routes.
ROUTES = (
    Route("company_home", 2, .80, .99),
    Route("company_about_contact", 2, .65, .98),
    Route("company_people", 2, .60, .98),
    Route("company_jobs", 2, .70, .97),
    Route("company_news_activity", 2, .55, .97),
    Route("sitemap_targeted", 1, .45, .98),
    Route("structured_data", 1, .35, .995),
    Route("licensed_search_discovery", 2, .50, .95),
)

HARD_REQUEST_BUDGET = 2000
EXTERNAL_COST_BUDGET = 10.0
PRECISION_GATE = 0.95


def choose_routes(*, requests_used: int, remaining_cost: float, has_verified_site: bool,
                  missing_fields: Iterable[str]) -> list[str]:
    """Return a deterministic route plan under the competition budgets."""
    missing = {x.casefold() for x in missing_fields}
    if not has_verified_site:
        return ["licensed_search_discovery"] if requests_used + 2 <= HARD_REQUEST_BUDGET and remaining_cost >= 0.02 else []
    wanted = []
    mapping = {
        "people": "company_people", "leadership": "company_people", "jobs": "company_jobs",
        "activity": "company_news_activity", "news": "company_news_activity",
        "website": "company_home", "contact": "company_about_contact",
    }
    for field, route in mapping.items():
        if field in missing and route not in wanted:
            wanted.append(route)
    # Always take cheap structured/sitemap passes before expensive discovery.
    for route in ("structured_data", "sitemap_targeted"):
        if route not in wanted:
            wanted.append(route)
    return wanted


def publishable_identity(*, org_match: bool, name_ratio: float, municipality_match: bool,
                         independent_signals: int = 0) -> bool:
    """Conservative identity firewall. No model-generated claim bypasses this."""
    if org_match:
        return True
    if name_ratio >= 1.0 and municipality_match:
        return True
    if name_ratio >= 0.95 and independent_signals >= 2:
        return True
    return False


def evidence_priority(kind: str) -> int:
    """Higher is better; used only for selecting among corroborating evidence."""
    return {
        "official_registry": 100, "official_filing": 98, "company_owned": 92,
        "licensed_public_source": 78, "public_news": 70, "social": 45,
        "search_snippet": 30,
    }.get(kind, 0)
