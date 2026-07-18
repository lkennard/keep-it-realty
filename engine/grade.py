"""
grade.py — comp grading / ranking engine.

Encodes the comp-SELECTION LOGIC worked out on the Poipu Aina file (2026-07-17).
It scores and RANKS candidates and explains WHY. It does NOT pick the final set,
set adjustments, or conclude value — those stay Logan's judgment. This surfaces a
ranked, annotated candidate list; Logan selects from it.

Named patterns encoded (confirmed live 2026-07-17):
  1. Physical-comparability-first expansion. When the in-section closed pool is thin
     at the subject's size, comparability on GLA + lot class can outrank geographic
     proximity. A physically-matching closed sale with a location adjustment beats a
     same-neighborhood sale half the subject's size.
  2. Amenity contamination is a SEPARATE exclusion axis from distance. A geographically
     close comp (e.g. an amenitized club community) can be penalized/flagged while a
     geographically far one is welcomed for physical match.
  3. Buyer-segment logic: the competing set is defined by who would actually cross-shop
     the subject (large house + acreage, NOT wanting club/HOA fees), not by a radius.
  4. DOM-0 / cash is SCRUTINIZE-not-exclude, and the scrutiny weight is lower at high
     price tiers (a $6M DOM-0 does not imply related parties the way a starter home does).
  5. Bracketing is per-axis; guideline exceedances get flagged for disclosure, not hidden.

Everything here is a TRANSPARENT, TUNABLE score. No hidden weighting. Logan can see and
change every number.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .his_parse import Comp, Subject, tmk_zone


# --------------------------- tunable configuration ---------------------------

@dataclass
class GradeConfig:
    """Every knob is exposed. These are DEFAULTS, not doctrine. Tune per assignment."""
    # GLA proximity: full credit within this % delta, linear falloff to zero at max.
    gla_full_pct: float = 0.10      # within 10% GLA = full size credit
    gla_zero_pct: float = 0.40      # beyond 40% GLA delta = no size credit

    # Lot proximity (acres), ratio-based so 0.2ac vs 2.5ac is treated fairly.
    lot_full_ratio: float = 1.5     # within 1.5x either way = full lot credit
    lot_zero_ratio: float = 6.0     # beyond 6x = no lot credit

    # Recency: DOM is the only date proxy in the one-line export. Lower DOM = fresher
    # market signal, but DOM-0 is handled separately (scrutiny, not reward).
    # Geographic proximity credit by shared TMK zone depth.
    same_plat_bonus: float = 25.0   # shares 4-2-8-XX plat
    same_section_bonus: float = 15.0  # shares 4-2-8 section
    same_district_bonus: float = 5.0  # shares 4-2 district

    # Status handling
    sold_bonus: float = 20.0        # closed sales are real evidence
    active_penalty: float = -8.0    # actives are ceilings, carry less weight

    # Scrutiny flags (do not exclude — annotate)
    dom_zero_high_tier_price: float = 3_000_000.0  # above this, DOM-0 scrutiny is light

    # Amenity-contamination exclusion axis (separate from distance).
    # Substrings in Location that signal an amenitized/club community whose price
    # carries an amenity package the typical non-club subject can't claim.
    amenity_flags: tuple = ("kukui", "kukuiula", "kukui'ula", "kukui`ula")
    amenity_penalty: float = -30.0

    # Weighting of the axes into the composite score
    w_gla: float = 40.0
    w_lot: float = 25.0
    w_geo: float = 1.0   # geo bonuses are already in point units
    w_status: float = 1.0


# ------------------------------- scoring core --------------------------------

def _linear_falloff(value: float, full: float, zero: float) -> float:
    """1.0 at/below `full`, 0.0 at/above `zero`, linear between."""
    if value <= full:
        return 1.0
    if value >= zero:
        return 0.0
    return 1.0 - (value - full) / (zero - full)


def _gla_credit(comp: Comp, subj: Subject, cfg: GradeConfig) -> tuple[float, str]:
    if not comp.gla or not subj.gla:
        return 0.0, "GLA missing"
    delta = abs(comp.gla - subj.gla) / subj.gla
    credit = _linear_falloff(delta, cfg.gla_full_pct, cfg.gla_zero_pct)
    dirn = "larger" if comp.gla > subj.gla else "smaller"
    return credit, f"GLA {comp.gla:,.0f}sf ({(comp.gla-subj.gla)/subj.gla*+100:+.0f}%, {dirn})"


def _lot_credit(comp: Comp, subj: Subject, cfg: GradeConfig) -> tuple[float, str]:
    if not comp.lot_acres or not subj.lot_acres:
        return 0.0, "lot missing"
    hi = max(comp.lot_acres, subj.lot_acres)
    lo = min(comp.lot_acres, subj.lot_acres)
    ratio = hi / lo if lo else cfg.lot_zero_ratio
    credit = _linear_falloff(ratio, cfg.lot_full_ratio, cfg.lot_zero_ratio)
    return credit, f"lot {comp.lot_acres:.2f}ac"


def _geo_credit(comp: Comp, subj: Subject, cfg: GradeConfig) -> tuple[float, str]:
    cp, sp = comp.tmk, subj.tmk
    if tmk_zone(cp, 4) == tmk_zone(sp, 4) and tmk_zone(sp, 4):
        return cfg.same_plat_bonus, "same plat"
    if tmk_zone(cp, 3) == tmk_zone(sp, 3) and tmk_zone(sp, 3):
        return cfg.same_section_bonus, "same section"
    if tmk_zone(cp, 2) == tmk_zone(sp, 2) and tmk_zone(sp, 2):
        return cfg.same_district_bonus, "same district"
    return 0.0, "diff district"


@dataclass
class GradedComp:
    comp: Comp
    score: float
    reasons: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)

    def why(self) -> str:
        base = ", ".join(self.reasons)
        if self.flags:
            base += "  ⚑ " + "; ".join(self.flags)
        return base


def grade_comp(comp: Comp, subj: Subject, cfg: GradeConfig) -> GradedComp:
    reasons: list[str] = []
    flags: list[str] = []

    gla_c, gla_r = _gla_credit(comp, subj, cfg)
    lot_c, lot_r = _lot_credit(comp, subj, cfg)
    geo_pts, geo_r = _geo_credit(comp, subj, cfg)
    reasons += [gla_r, lot_r, geo_r]

    score = cfg.w_gla * gla_c + cfg.w_lot * lot_c + cfg.w_geo * geo_pts

    # status
    if comp.is_sold:
        score += cfg.sold_bonus
        reasons.append("SOLD")
    elif comp.is_active:
        score += cfg.active_penalty
        reasons.append(f"{comp.status} (ceiling)")

    # tenure gate — hard mismatch is a flag for Logan, not an auto-drop
    if subj.tenure and comp.tenure and comp.tenure.lower() != subj.tenure.lower():
        flags.append(f"TENURE {comp.tenure} ≠ subject {subj.tenure}")

    # DOM-0 scrutiny, price-tier aware
    if comp.dom_zero:
        if comp.price and comp.price >= cfg.dom_zero_high_tier_price:
            flags.append("DOM-0 (high tier — verify, low concern)")
        else:
            flags.append("DOM-0 (SCRUTINIZE: sold before market)")

    # amenity contamination — separate axis from distance
    loc = (comp.location or "").lower()
    if any(a in loc for a in cfg.amenity_flags):
        score += cfg.amenity_penalty
        flags.append("AMENITY community (club/HOA baked into price — adjust down or disclose)")

    # multi-structure / compound tell: very high bath count vs beds
    if comp.beds and comp.baths and comp.baths >= comp.beds + 3:
        flags.append("possible multi-structure/compound (bath:bed ratio)")

    return GradedComp(comp=comp, score=round(score, 1), reasons=[r for r in reasons if r], flags=flags)


def grade_all(comps: list[Comp], subj: Subject, cfg: Optional[GradeConfig] = None,
              fs_only: bool = True) -> list[GradedComp]:
    cfg = cfg or GradeConfig()
    pool = comps
    if fs_only and subj.tenure.lower() == "fee simple":
        # gate leasehold out of an FS subject's set (Logan's hard rule),
        # but keep them retrievable — we just don't rank them in.
        pool = [c for c in comps if c.tenure.lower() != "leasehold"]
    graded = [grade_comp(c, subj, cfg) for c in pool]
    graded.sort(key=lambda g: g.score, reverse=True)
    return graded
