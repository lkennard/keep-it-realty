"""
narrative.py — per-comp narrative + disclosure generator, in Logan's voice.

Encoded from the real Uluwehi/Anini/Kawaihau report language (2026-07). Given a comp
and the adjustments LOGAN SET, this drafts the narrative the way Logan writes it. It
does NOT decide adjustments or value — it renders language that MATCHES the numbers
Logan already set, so grid and prose can never drift.

Logan's per-comp narrative structure (observed, verbatim pattern):
  [recency/location] + [GLA delta, QUALITATIVE not exact-SF] + [condition/quality tier:
  equivalent or superior/inferior with specifics] + [adjustments IN WORDS, no $ figures]
  + [bracketing role].

Hard voice rules extracted from real reports:
  - Adjustments described in WORDS, never dollar figures, in per-comp narrative.
  - GLA differences described qualitatively ("larger/smaller", "brackets the high end"),
    not as exact square footage in the narrative sentence.
  - When a comp shares the subject's Q or C rating but still gets an adjustment, the
    narrative MUST state the adjustment reflects differences WITHIN the same rating category.
  - Guideline exceedances get a dedicated disclosure naming each comp and each threshold.
  - Formal-professional register (distinct from Logan's casual chat voice). No em dashes.
"""
from __future__ import annotations
from .mismo_model import CompSale, Report


# Guideline thresholds (standard; tunable per assignment)
NET_GUIDELINE = 15.0
GROSS_GUIDELINE = 25.0
SINGLE_ADJ_PCT_GUIDELINE = 10.0


def _qual_gla(comp: CompSale, subj_gla: float) -> str:
    """Qualitative GLA phrasing, never raw SF in the sentence."""
    if not comp.gla or not subj_gla:
        return "a comparable gross living area"
    d = (comp.gla - subj_gla) / subj_gla
    if abs(d) <= 0.05:
        return "a gross living area similar to the subject"
    if d > 0:
        strength = "substantially larger" if d > 0.15 else "a larger"
        return f"{strength} gross living area than the subject, bracketing the upper end of living area"
    strength = "substantially smaller" if d < -0.15 else "a smaller"
    return f"{strength} gross living area than the subject"


def _rating_phrase(comp_rating: str, subj_rating: str, label: str) -> str:
    """Quality/condition tier comparison. Flags same-rating-adjustment need."""
    if not comp_rating or not subj_rating:
        return ""
    if comp_rating == subj_rating:
        return f"equivalent {comp_rating} {label}"
    # superior/inferior by the numeric part (C2 superior to C3; Q3 superior to Q4)
    try:
        cn = int("".join(ch for ch in comp_rating if ch.isdigit()))
        sn = int("".join(ch for ch in subj_rating if ch.isdigit()))
    except ValueError:
        return f"{comp_rating} {label}"
    if cn < sn:
        return f"a superior {comp_rating} {label} relative to the subject's {subj_rating}"
    return f"an inferior {comp_rating} {label} relative to the subject's {subj_rating}"


def _adjusted_rows_in_words(comp: CompSale) -> list[str]:
    """List the grid rows that carry a non-zero adjustment, described in words."""
    words = []
    label_map = {
        "Location": "location", "SiteArea": "site", "View": "view",
        "GrossLivingArea": "gross living area", "Condition": "condition",
        "Quality": "quality", "CarStorage": "garage", "PorchDeck": "porch/deck",
        "Age": "age", "EnergyEfficient": "energy-efficient features",
    }
    for a in comp.adjustments:
        if a.amount:  # non-zero, non-blank
            words.append(label_map.get(a.kind, a.kind.lower()))
    return words


def per_comp_narrative(comp: CompSale, subject: CompSale, is_most_recent: bool = False,
                       same_rating_adjusted: bool = False) -> str:
    """Draft one comparable's narrative paragraph in Logan's voice."""
    subj_gla = subject.gla or 0
    parts: list[str] = []

    # Opening: identity + recency/location
    lead = f"Comparable #{comp.seq} ({comp.address})"
    if is_most_recent:
        parts.append(
            f"{lead} is the most recent closed sale in the competing segment as of the "
            f"effective date and provides the strongest date-of-sale support in a segment "
            f"with limited recent closings."
        )
    else:
        parts.append(f"{lead} is a closed sale within the subject's competing market segment.")

    # GLA (qualitative)
    parts.append(f"It offers {_qual_gla(comp, subj_gla)}.")

    # Quality + condition tiers
    q = _rating_phrase(comp.quality, subject.quality, "quality")
    c = _rating_phrase(comp.condition, subject.condition, "condition")
    tier = ", ".join([p for p in (q, c) if p])
    if tier:
        parts.append(f"The sale reflects {tier}.")

    # Same-rating-adjustment disclosure (Logan's hard rule)
    if same_rating_adjusted:
        parts.append(
            "As the comparable carries the same overall rating category as the subject, "
            "the applied adjustment reflects differences within the same rating category."
        )

    # Adjustments in words (no dollar figures)
    adj_words = _adjusted_rows_in_words(comp)
    if adj_words:
        if len(adj_words) == 1:
            parts.append(f"An adjustment was applied for {adj_words[0]}.")
        else:
            parts.append(
                f"Adjustments were applied for {', '.join(adj_words[:-1])} and {adj_words[-1]}."
            )
    else:
        parts.append("The sale required minimal adjustment.")

    return " ".join(parts)


def guideline_disclosure(comps: list[CompSale]) -> str:
    """Molo-style guideline-exceedance disclosure, naming each comp and threshold."""
    net_flags, gross_flags = [], []
    for c in comps:
        npct, gpct = c.net_pct(), c.gross_pct()
        if npct is not None and abs(npct) > NET_GUIDELINE:
            net_flags.append((c, abs(npct)))
        if gpct is not None and gpct > GROSS_GUIDELINE:
            gross_flags.append((c, gpct))
    if not net_flags and not gross_flags:
        return ""

    lines = ["Note Regarding Adjustment Guidelines:"]
    if net_flags:
        seg = "; ".join(f"Comparable #{c.seq} ({p:.1f}%)" for c, p in net_flags)
        lines.append(
            f"Net adjustments to {seg} exceed the typical {NET_GUIDELINE:.0f}% net guideline."
        )
    if gross_flags:
        seg = "; ".join(f"Comparable #{c.seq} ({p:.1f}%)" for c, p in gross_flags)
        lines.append(
            f"Gross adjustments to {seg} exceed the typical {GROSS_GUIDELINE:.0f}% gross guideline."
        )
    lines.append(
        "These exceedances result directly from the subject's market segment, which contains "
        "a limited number of closed transactions spanning a wide range of product, such that the "
        "most proximate and most recent sales are not always the most physically similar. All "
        "adjustments applied are derived from market data. The use of these comparables is "
        "reasonable and necessary to bracket the subject in a thin market, as disclosed."
    )
    return " ".join(lines)


def weighting_block(report: Report) -> str:
    """Weighting summary in Logan's pattern: adjusted price + weight + rationale per comp,
    with the arithmetic shown and the narrative ranking mirroring the percentages."""
    v = report.valuation
    if not v or not v.weights:
        return "[Weighting not yet set — enter weights to generate this block.]"
    lines = ["Summary and Weighting of Adjusted Sale Prices:"]
    weighted_sum = 0.0
    for c in report.comps:
        w = v.weights.get(c.seq)
        ap = c.adjusted_price()
        if w is None or ap is None:
            continue
        weighted_sum += ap * (w / 100.0)
        lines.append(f"Comparable #{c.seq} ({c.address}), adjusted to ${ap:,.0f}, "
                     f"was given {w:.0f}% weight.")
    lines.append(f"The weighted indication is ${weighted_sum:,.0f}, "
                 f"reconciled to a final opinion of value of ${v.appraised_value:,.0f}.")
    # dependency-chain guard: does weighting math tie to the stated conclusion?
    drift = abs(weighted_sum - v.appraised_value)
    if drift > max(5000, v.appraised_value * 0.005):
        lines.append(f"[⚑ LINT: weighted indication ${weighted_sum:,.0f} differs from stated "
                     f"conclusion ${v.appraised_value:,.0f} by ${drift:,.0f} — verify weights/rounding.]")
    return " ".join(lines)
