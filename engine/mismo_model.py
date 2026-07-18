"""
mismo_model.py — version-INDEPENDENT valuation model.

This is the intermediate representation between Logan's engine (graded comps +
his adjustments) and the on-disk format. It knows nothing about 2.6 vs 3.6.
Serializers (serialize_26.py now, serialize_36.py in November) render it.

Design goal stated by Logan (2026-07-17): finish 2.6 now, swap to 3.6 later as a
new serializer, NOT a rewrite. So all format-specific strings (GSE enums, element
names) live in the serializers; this model holds plain appraisal data.

Scope boundary: this holds the numbers Logan SET. It computes nothing on its own
beyond arithmetic he'd do by hand (adjusted price = sale price + sum of adjustments).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# The canonical UAD adjustment-grid rows, in TOTAL's order. Value = the _Type string.
GRID_ROWS = [
    "SalesConcessions", "FinancingConcessions", "DateOfSale", "Location",
    "PropertyRights", "SiteArea", "View", "DesignStyle", "Quality", "Age",
    "Condition", "GrossLivingArea", "BasementArea", "BasementFinish",
    "FunctionalUtility", "HeatingCooling", "EnergyEfficient", "CarStorage",
    "PorchDeck",
]


@dataclass
class Adjustment:
    """One grid row for one comp. `description` is the UAD-coded cell value
    (e.g. 'N;Res;' or 'Q3'); `amount` is the dollar adjustment Logan set (may be None/blank)."""
    kind: str                      # one of GRID_ROWS, or 'Other'
    description: str = ""
    amount: Optional[int] = None   # +/- dollars; None renders as blank (no adjustment)
    other_label: Optional[str] = None  # for kind='Other' (e.g. 'Pool/Spa', 'TMK')


@dataclass
class CompSale:
    """A comparable sale. Facts come from the MLS pull (engine); adjustments from Logan."""
    seq: int
    address: str
    city_state_zip: str = ""
    sale_price: Optional[int] = None
    gla: Optional[float] = None
    tmk: str = ""
    mls_number: str = ""
    dom: Optional[int] = None
    beds: Optional[int] = None
    baths: Optional[float] = None
    total_rooms: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    proximity: str = ""            # 'x.xx miles SE'
    sale_type: str = "ArmsLengthSale"
    financing: str = "Cash"
    quality: str = ""              # Q rating
    condition: str = ""            # C rating
    view_rating: str = "Neutral"   # GSE enum: Beneficial/Neutral/Adverse
    location_rating: str = "Neutral"
    data_source_verification: str = "County Records"
    adjustments: list[Adjustment] = field(default_factory=list)
    other_features: list[Adjustment] = field(default_factory=list)  # Pool/Spa, TMK, etc.
    prior_sale_comment: str = ""

    # --- the only arithmetic: adjusted price = sale price + sum of adjustments ---
    def net_adjustment(self) -> int:
        total = 0
        for a in list(self.adjustments) + list(self.other_features):
            if a.amount:
                total += a.amount
        return total

    def adjusted_price(self) -> Optional[int]:
        if self.sale_price is None:
            return None
        return self.sale_price + self.net_adjustment()

    def gross_pct(self) -> Optional[float]:
        if not self.sale_price:
            return None
        gross = sum(abs(a.amount) for a in (self.adjustments + self.other_features) if a.amount)
        return round(gross / self.sale_price * 100, 1)

    def net_pct(self) -> Optional[float]:
        if not self.sale_price:
            return None
        return round(self.net_adjustment() / self.sale_price * 100, 1)

    def price_per_gla(self) -> Optional[float]:
        if self.sale_price and self.gla:
            return round(self.sale_price / self.gla, 2)
        return None


@dataclass
class Valuation:
    """The reconciled conclusion Logan set, plus the weighting behind it (for the addendum)."""
    appraised_value: int
    effective_date: str            # YYYY-MM-DD
    weights: dict = field(default_factory=dict)  # {seq: weight_pct} — optional, for narrative

    def check_propagation(self) -> dict:
        """Return the value that must appear in every propagation location.
        The dependency-chain guard: one number, surfaced so the lint layer can verify
        it matches everywhere before export."""
        return {"appraised_value": self.appraised_value}


@dataclass
class Report:
    file_number: str
    form_type: str = "FNM1004"
    purpose: str = "Refinance"
    subject_address: str = ""
    subject_city_state_zip: str = ""
    appraiser_signed_date: str = ""
    subject: Optional[CompSale] = None      # seq 0
    comps: list[CompSale] = field(default_factory=list)
    valuation: Optional[Valuation] = None
    sales_comparison_comment: str = ""
