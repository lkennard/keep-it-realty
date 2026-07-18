"""
enrich.py — value-add helpers that run on the richer dated export.

1. remarks_flags: scans agent + public remarks for features that may need bracketing
   (pool, ADU, solar/PV, ocean view, renovated, etc.). Keywords stay VISIBLE to aid
   Logan's comp selection — they are NOT auto-categorized into adjustments.
2. to_mc_records: turns parsed Comps into MCRecord objects for the 1004MC engine,
   filtered to the subject's competing segment.

Scope boundary: surfaces information for Logan's judgment. Sets no adjustments.
"""
from __future__ import annotations
from .his_parse import Comp
from .market_conditions import MCRecord

# Feature keywords worth flagging for bracketing (from Logan's stated comp-search needs)
REMARK_KEYWORDS = {
    "pool": ["pool", "swimming pool"],
    "spa": ["spa", "hot tub", "jacuzzi"],
    "adu/ohana": ["adu", "ohana", "guest house", "guest cottage", "second dwelling", "accessory dwelling"],
    "solar/pv": ["photovoltaic", "pv system", "solar panel", "solar system", "tesla powerwall"],
    "ocean view": ["ocean view", "oceanfront", "ocean vista", "pacific ocean", "coastline view"],
    "renovated": ["renovated", "remodeled", "newly updated", "new construction", "custom-built", "custom built"],
    "cpr": ["cpr", "condominium property regime"],
}


def remarks_flags(comp: Comp) -> list[str]:
    """Return the feature tags found in a comp's remarks. Visible aid, not an adjustment."""
    text = f"{comp.agent_remarks} {comp.public_remarks}".lower()
    if not text.strip():
        return []
    hits = []
    for tag, terms in REMARK_KEYWORDS.items():
        if any(t in text for t in terms):
            hits.append(tag)
    return hits


def to_mc_records(comps: list[Comp], gla_min: float = 2500.0,
                  fee_simple_only: bool = True) -> list[MCRecord]:
    """Build 1004MC records from parsed comps, filtered to the subject's competing segment.
    Best practice: same segment as subject, not the whole neighborhood."""
    records: list[MCRecord] = []
    for c in comps:
        if fee_simple_only and c.tenure.lower() != "fee simple":
            continue
        if gla_min and (c.gla or 0) < gla_min:
            continue
        records.append(MCRecord(
            status=c.status,
            price=c.price,
            gla=c.gla,
            dom=c.dom,
            close_date=c.sold_date if c.status.lower() == "sold" else None,
        ))
    return records
