"""
market_conditions.py — 1004MC / One-Unit Housing Trends engine.

Built to documented best practice (Fannie 1004MC guidance + appraiser-forum consensus,
verified 2026-07-17):
  - The 1004MC reflects the SUBJECT'S COMPETING SEGMENT, not the whole neighborhood.
    "Sales and listings must be properties that compete with the subject property,
    determined by the criteria a prospective buyer of the subject would use."
  - Trend CONCLUSIONS here must match the page-1 Neighborhood One-Unit Housing Trends.
  - Thin buckets are DISCLOSED, never invented. "You can't base a trend on 1-3 sales."
  - Comps in the grid may come from competing markets that do NOT appear here; that is
    the documented reality of a segmented thin market, not a contradiction.

HARD DATA REQUIREMENT: time-bucketing needs a SALE/CLOSE DATE per record. The HIS
one-line export does not carry it. This engine requires a dated pull; without dates it
emits structure + an explicit "awaiting dated MLS pull" flag rather than fabricating trends.

Scope boundary: computes market statistics from public MLS data. The appraiser concludes
the trend direction (Increasing/Stable/Declining) — this surfaces the numbers that support it.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import statistics


@dataclass
class MCRecord:
    """One sale/listing in the competing segment, WITH a date (required for bucketing)."""
    status: str                 # Sold / Active / Pending
    price: Optional[float]
    gla: Optional[float]
    dom: Optional[int]
    close_date: Optional[date]  # REQUIRED for solds; None for actives
    list_date: Optional[date] = None


@dataclass
class MCBucket:
    label: str
    n_sales: int = 0
    n_listings: int = 0
    median_price: Optional[float] = None
    median_dom: Optional[int] = None
    absorption_per_month: Optional[float] = None
    months: int = 3
    thin: bool = False           # True when too few sales to trust a trend


def _median(vals: list[float]) -> Optional[float]:
    vals = [v for v in vals if v is not None]
    return statistics.median(vals) if vals else None


def compute_bucket(records: list[MCRecord], label: str, months: int,
                   start: date, end: date, thin_threshold: int = 4) -> MCBucket:
    sold = [r for r in records if r.status.lower() == "sold" and r.close_date
            and start <= r.close_date <= end]
    listings = [r for r in records if r.status.lower() in ("active", "pending", "contingent")]
    b = MCBucket(label=label, months=months)
    b.n_sales = len(sold)
    b.n_listings = len(listings)
    b.median_price = _median([r.price for r in sold])
    doms = [r.dom for r in sold if r.dom is not None]
    b.median_dom = int(statistics.median(doms)) if doms else None
    b.absorption_per_month = round(len(sold) / months, 2) if months else None
    b.thin = b.n_sales < thin_threshold
    return b


@dataclass
class MarketConditions:
    buckets: list[MCBucket] = field(default_factory=list)
    has_dates: bool = True
    segment_description: str = ""

    def trend_note(self) -> str:
        """Draft the MC commentary. Discloses thin buckets; states the appraiser must
        conclude the trend direction. Never asserts a trend the data can't support."""
        if not self.has_dates:
            return ("[1004MC AWAITING DATED MLS PULL: the one-line export lacks sale/close "
                    "dates required for time-bucketed absorption and median-trend analysis. "
                    "Provide a neighborhood-segment pull that includes closing dates to compute "
                    "this section to best practice.]")
        lines = [f"The One-Unit Housing Trends analysis reflects the subject's competing segment "
                 f"({self.segment_description})."]
        thin = [b for b in self.buckets if b.thin]
        if thin:
            names = ", ".join(b.label for b in thin)
            lines.append(
                f"The {names} period(s) contain limited closed sales, consistent with the thin "
                f"transaction volume typical of this market segment. Where sales are too few to "
                f"establish a statistically reliable trend, the analysis is supplemented by "
                f"broader segment observation and disclosed accordingly, rather than deriving a "
                f"trend from an insufficient sample."
            )
        lines.append("[Appraiser concludes trend direction (Increasing/Stable/Declining); the "
                     "conclusion here must match the page-1 Neighborhood One-Unit Housing Trends.]")
        return " ".join(lines)


def build_market_conditions(records: list[MCRecord], as_of: date,
                            segment_description: str) -> MarketConditions:
    """Standard 1004MC buckets: Current 0-3mo, Prior 4-6mo, Prior 7-12mo."""
    has_dates = any(r.close_date for r in records if r.status.lower() == "sold")
    if not has_dates:
        return MarketConditions(buckets=[], has_dates=False,
                                segment_description=segment_description)

    from datetime import timedelta
    def months_ago(m): return date(as_of.year - (m // 12), ((as_of.month - m - 1) % 12) + 1, 1)

    mc = MarketConditions(has_dates=True, segment_description=segment_description)
    mc.buckets = [
        compute_bucket(records, "Current (0-3 mo)", 3, months_ago(3), as_of),
        compute_bucket(records, "Prior (4-6 mo)", 3, months_ago(6), months_ago(3)),
        compute_bucket(records, "Prior (7-12 mo)", 6, months_ago(12), months_ago(6)),
    ]
    return mc
