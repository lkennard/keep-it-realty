"""
assignment_poipu_aina.py — live assignment scaffold.

Subject + the six selected comps as data. ADJUSTMENT AMOUNTS AND WEIGHTS ARE BLANK
by design — those are Logan's valuation judgment. Fill the `amount=` fields and the
`weights` dict, then run generate_poipu.py to emit narratives + importable XML.

Comp selection locked 2026-07-17 (Logan's picks):
  1. Poipu Aina sibling  — location/lot/tenure anchor
  2. 5350 Kalalea View #8D — best physical match
  3. 5450 Kalalea View     — large-custom bracket
  4. 5330 Kalalea View #7D — post-improvement resale (the $5.495M sale, not the $4.8M)
  5. 2970 Kahalawai        — disclosed SF/quality upper bracket (Kukuiula, amenity-adj)
  6. 2690 Halalu           — Poipu corridor lower bracket

BENCH (not in grid, kept for easy swap): 5330 base $4.8M; south actives
  2551-E Ala Kinoiki, Makahuena Estates.

Subject GLA = 4,532 ASSUMED pending Logan's verification (tax card shows 3,524 main +
1,008 second-story frame). Update `subject.gla` when verified.
"""
from engine.mismo_model import CompSale, Adjustment, Valuation, Report

# --------------------------------- SUBJECT ---------------------------------
subject = CompSale(
    seq=0,
    address="Poipu Aina Pl (Ala Kinoiki)",
    city_state_zip="Koloa, HI 96756",
    gla=4532,                 # ASSUMED — verify
    tmk="(4)-2-8-22-31",
    beds=None, baths=None,    # fill from inspection
    quality="",               # Logan sets subject Q
    condition="",             # Logan sets subject C
)

# --------------------------------- COMPS -----------------------------------
# Facts are from the HIS pulls. amount= fields are BLANK for Logan to set.

comp1 = CompSale(
    seq=1, address="1740-C Poipu Aina Pl", city_state_zip="Koloa, HI 96756",
    sale_price=4_000_000, gla=2928, tmk="(4)-2-8-22-31-1", dom=0,
    data_source_verification="County Records; verify arm's-length (DOM-0, high tier)",
    adjustments=[
        Adjustment("Location", "", amount=None),
        Adjustment("SiteArea", "2.47 ac", amount=None),
        Adjustment("GrossLivingArea", "2928", amount=None),
        Adjustment("Quality", "", amount=None),
        Adjustment("Condition", "", amount=None),
    ],
    other_features=[Adjustment("Other", description="(4)-2-8-22-31-1", amount=0)],
    prior_sale_comment="Same CPR map as subject; arm's-length per Logan; prior 2024 sale ~$3.9M with market exposure.",
)

comp2 = CompSale(
    seq=2, address="5350 Kalalea View Dr #8D", city_state_zip="Anahola, HI 96703",
    sale_price=6_495_000, gla=4506, dom=169,
    adjustments=[
        Adjustment("Location", "", amount=None),   # north-shore location adj
        Adjustment("SiteArea", "4.58 ac", amount=None),
        Adjustment("GrossLivingArea", "4506", amount=None),
    ],
    prior_sale_comment="Best physical match: near-exact GLA, large lot.",
)

comp3 = CompSale(
    seq=3, address="5450 Kalalea View Dr", city_state_zip="Anahola, HI 96703",
    sale_price=8_450_000, gla=4220, dom=56,
    adjustments=[
        Adjustment("Location", "", amount=None),
        Adjustment("SiteArea", "1.50 ac", amount=None),
        Adjustment("GrossLivingArea", "4220", amount=None),
    ],
)

comp4 = CompSale(
    seq=4, address="5330 Kalalea View Dr #7D", city_state_zip="Anahola, HI 96703",
    sale_price=5_495_000, gla=4156, dom=68,
    adjustments=[
        Adjustment("Location", "", amount=None),
        Adjustment("SiteArea", "4.63 ac", amount=None),
        Adjustment("GrossLivingArea", "4156", amount=None),
        Adjustment("Condition", "", amount=None),   # post-improvement resale
    ],
    prior_sale_comment="Resale; improvements made between sales. $5.495M sale reflects improved condition.",
)

comp5 = CompSale(
    seq=5, address="2970 Kahalawai St", city_state_zip="Koloa, HI 96756",
    sale_price=8_100_000, gla=4659, dom=0,
    data_source_verification="County Records; verify (DOM-0/cash, high tier)",
    adjustments=[
        Adjustment("Location", "", amount=None),   # Kukuiula amenity/club adjustment (down)
        Adjustment("SiteArea", "0.61 ac", amount=None),
        Adjustment("GrossLivingArea", "4659", amount=None),
    ],
    prior_sale_comment="Kukuiula; disclosed upper GLA/quality bracket; carries club/amenity package requiring downward adjustment.",
)

comp6 = CompSale(
    seq=6, address="2690 Halalu St", city_state_zip="Koloa, HI 96756",
    sale_price=3_950_000, gla=3057, dom=78,
    adjustments=[
        Adjustment("Location", "", amount=None),
        Adjustment("SiteArea", "0.36 ac", amount=None),
        Adjustment("GrossLivingArea", "3057", amount=None),
    ],
    prior_sale_comment="Poipu corridor lower bracket.",
)

# ------------------------------- VALUATION ---------------------------------
# WEIGHTS BLANK — Logan sets. appraised_value BLANK until reconciled.
valuation = Valuation(
    appraised_value=0,           # Logan sets after adjustments
    effective_date="2026-07-17",
    weights={},                  # e.g. {1:20, 2:20, 3:15, 4:15, 5:10, 6:20}
)

report = Report(
    file_number="[assign]",
    subject_address=subject.address,
    subject_city_state_zip=subject.city_state_zip,
    subject=subject,
    comps=[comp1, comp2, comp3, comp4, comp5, comp6],
    valuation=valuation,
)
