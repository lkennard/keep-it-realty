"""Prove the serializer reproduces TOTAL's real output. Rebuild comp #1 from the
Uluwehi file as model objects, serialize, and check the dependency-chain math and
structure against the known-good values TOTAL emitted."""
from engine.mismo_model import CompSale, Adjustment
from engine.serialize_26 import serialize_comparable_sale
import xml.dom.minidom as minidom

# Comp #1 from 2767_Uluwehi_St.xml — 5105 Lau Nahele St
# TOTAL's real values: sale 5,000,000; net +66,700; adjusted 5,066,700; gross 4.7%; net 1.3%
c1 = CompSale(
    seq=1,
    address="5105 Lau Nahele St",
    city_state_zip="Koloa, HI 96756",
    sale_price=5_000_000,
    gla=2836,
    mls_number="721806",
    dom=188,
    beds=4, baths=4.1, total_rooms=6,
    latitude=21.8857789, longitude=-159.474096,
    proximity="0.21 miles SE",
    quality="Q3", condition="C2",
    view_rating="Beneficial", location_rating="Neutral",
    adjustments=[
        Adjustment("SalesConcessions", "ArmLth"),
        Adjustment("FinancingConcessions", "Cash;0"),
        Adjustment("DateOfSale", "s04/26;c12/25"),
        Adjustment("Location", "N;Res;", amount=+150000),
        Adjustment("PropertyRights", "Fee Simple"),
        Adjustment("SiteArea", "14191 sf", amount=-11700),
        Adjustment("View", "B;Part Ocean;"),
        Adjustment("DesignStyle", "DT2;Traditional", amount=0),
        Adjustment("Quality", "Q3"),
        Adjustment("Age", "10", amount=0),
        Adjustment("Condition", "C2"),
        Adjustment("GrossLivingArea", "2836", amount=-71600),
        Adjustment("EnergyEfficient", "None", amount=0),
        Adjustment("PorchDeck", "Deck", amount=0),
    ],
    other_features=[
        Adjustment("Other", description="Pool/Spa"),
        Adjustment("Other", description="(4)-2-6-16-29", amount=0),
    ],
)

print("=== DEPENDENCY-CHAIN MATH CHECK (ours vs TOTAL's real output) ===")
checks = [
    ("net adjustment", c1.net_adjustment(), 66700),
    ("adjusted price", c1.adjusted_price(), 5066700),
    ("net %",          c1.net_pct(),        1.3),
    ("gross %",        c1.gross_pct(),      4.7),
    ("$/GLA",          c1.price_per_gla(),  1763.05),
]
allpass = True
for label, ours, total in checks:
    ok = "PASS" if abs(float(ours) - float(total)) < 0.06 else "FAIL"
    if ok == "FAIL": allpass = False
    print(f"  [{ok}] {label:16} ours={ours:<12} TOTAL={total}")

print()
print("=== SERIALIZED COMPARABLE_SALE (ours) ===")
xml = serialize_comparable_sale(c1)
print(minidom.parseString(xml).toprettyxml(indent="  ")[:1600])

print("RESULT:", "ALL MATH MATCHES TOTAL" if allpass else "MISMATCH — needs fix")
