"""
his_parse.py — HIS (Hawaii Information Service) one-line CSV parser + normalizer.

This is the shared input layer. Today it reads the manual ctrl-A / one-line CSV
export. Later, the VOW RESO API adapter produces the SAME normalized Comp objects,
so nothing downstream changes when the feed comes online.

Scope boundary: this module only READS and STRUCTURES public MLS data.
It makes no valuation judgment.
"""
from __future__ import annotations
import csv
import re
from dataclasses import dataclass, field, asdict
from typing import Optional


# ----------------------------- value coercion -----------------------------

def _num(s: Optional[str]) -> Optional[float]:
    """Pull the first numeric value out of a messy string. '$3,950,000' -> 3950000.0"""
    if not s:
        return None
    d = re.sub(r"[^0-9.]", "", s)
    if d in ("", "."):
        return None
    try:
        return float(d)
    except ValueError:
        return None


def _acres(s: Optional[str]) -> Optional[float]:
    """
    HIS 'Lnd Area' comes as either '10,499 sqft' or a bare acreage.
    Normalize everything to ACRES so the engine compares apples to apples.
    """
    if not s:
        return None
    v = _num(s)
    if v is None:
        return None
    if "sqft" in s.lower() or "sq ft" in s.lower():
        return v / 43560.0
    # Bare number: HIS bare land area on residential is typically already acres.
    return v


def _dom(s: Optional[str]) -> Optional[int]:
    v = _num(s)
    return int(v) if v is not None else None


def tmk_parts(tmk: str) -> list[str]:
    return [p for p in (tmk or "").split("-") if p != ""]


def tmk_zone(tmk: str, depth: int = 3) -> str:
    """Zone prefix, default plat-level: '4-2-8-22-31-1' -> '4-2-8'."""
    return "-".join(tmk_parts(tmk)[:depth])


# ------------------------------- data model -------------------------------

@dataclass
class Comp:
    mls: str
    tmk: str
    status: str
    dom: Optional[int]
    price: Optional[float]
    tenure: str
    beds: Optional[float]
    baths: Optional[float]
    location: str
    lot_acres: Optional[float]
    gla: Optional[float]
    raw: dict = field(default_factory=dict)

    @property
    def zone(self) -> str:
        return tmk_zone(self.tmk)

    @property
    def is_sold(self) -> bool:
        return self.status.strip().lower() == "sold"

    @property
    def is_active(self) -> bool:
        return self.status.strip().lower() in ("active", "preview", "contingent", "under contract")

    @property
    def dom_zero(self) -> bool:
        return self.dom == 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        d["zone"] = self.zone
        return d


@dataclass
class Subject:
    """The subject is entered by Logan at intake. No judgment encoded here."""
    address: str
    tmk: str
    gla: float
    lot_acres: float
    tenure: str = "Fee Simple"
    beds: Optional[float] = None
    baths: Optional[float] = None
    year_built: Optional[int] = None
    quality: Optional[str] = None      # UAD Q rating, Logan-set
    condition: Optional[str] = None    # UAD C rating, Logan-set

    @property
    def zone(self) -> str:
        return tmk_zone(self.tmk)


# ------------------------------- the parser -------------------------------

# HIS one-line export header (locked from real files, 2026-07):
# MLS#,TMK,Type,Status,DOM,Price,Lnd Tnr,Beds,Baths,Location,Lnd Area,Living Area,Primary Listor,...
HIS_FIELD_MAP = {
    "mls": "MLS#",
    "tmk": "TMK",
    "status": "Status",
    "dom": "DOM",
    "price": "Price",
    "tenure": "Lnd Tnr",
    "beds": "Beds",
    "baths": "Baths",
    "location": "Location",
    "lot": "Lnd Area",
    "gla": "Living Area",
}


def parse_his_csv(path: str) -> list[Comp]:
    """Read an HIS one-line CSV export into normalized Comp objects.
    Silently drops the blank separator/footer rows HIS appends."""
    comps: list[Comp] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            mls = (row.get(HIS_FIELD_MAP["mls"]) or "").strip()
            if not mls:
                continue  # blank/footer row
            comps.append(Comp(
                mls=mls,
                tmk=(row.get(HIS_FIELD_MAP["tmk"]) or "").strip(),
                status=(row.get(HIS_FIELD_MAP["status"]) or "").strip(),
                dom=_dom(row.get(HIS_FIELD_MAP["dom"])),
                price=_num(row.get(HIS_FIELD_MAP["price"])),
                tenure=(row.get(HIS_FIELD_MAP["tenure"]) or "").strip(),
                beds=_num(row.get(HIS_FIELD_MAP["beds"])),
                baths=_num(row.get(HIS_FIELD_MAP["baths"])),
                location=(row.get(HIS_FIELD_MAP["location"]) or "").strip(),
                lot_acres=_acres(row.get(HIS_FIELD_MAP["lot"])),
                gla=_num(row.get(HIS_FIELD_MAP["gla"])),
                raw=dict(row),
            ))
    return comps


if __name__ == "__main__":
    import sys
    comps = parse_his_csv(sys.argv[1])
    print(f"Parsed {len(comps)} comps")
    from collections import Counter
    print("Status:", dict(Counter(c.status for c in comps)))
    print("Zones:", dict(Counter(c.zone for c in comps)))
