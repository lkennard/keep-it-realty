"""End-to-end demo: shows that setting adjustments drives narratives + XML + math
off ONE source. Numbers here are PLACEHOLDER (clearly not Logan's real judgment) —
just to prove the machine runs. Logan replaces these in assignment_poipu_aina.py."""
from assignment_poipu_aina import report, subject
from engine.narrative import per_comp_narrative, guideline_disclosure, weighting_block

# --- PLACEHOLDER adjustments just to demonstrate propagation (NOT real valuation) ---
subject.quality = "Q4"; subject.condition = "C2"
demo = {
    1: {"Location": +200000, "GrossLivingArea": +640000, "Condition": None, "Quality": None, "SiteArea": 0},
    2: {"Location": -300000, "GrossLivingArea": +130000, "SiteArea": -100000},
    3: {"Location": -300000, "GrossLivingArea": +470000, "SiteArea": 0},
    4: {"Location": -250000, "GrossLivingArea": +560000, "Condition": +150000, "SiteArea": 0},
    5: {"Location": -1500000, "GrossLivingArea": -50000, "SiteArea": +200000},
    6: {"Location": +100000, "GrossLivingArea": +590000, "SiteArea": +100000},
}
for c in report.comps:
    for a in c.adjustments:
        if c.seq in demo and a.kind in demo[c.seq]:
            a.amount = demo[c.seq][a.kind]
    c.quality = c.quality or "Q4"
    c.condition = c.condition or "C2"

report.valuation.weights = {1:20, 2:20, 3:15, 4:15, 5:10, 6:20}

# reconcile to weighted sum (placeholder)
ws = sum(c.adjusted_price()*(report.valuation.weights[c.seq]/100) for c in report.comps)
report.valuation.appraised_value = round(ws/1000)*1000

print("="*70)
print("DEPENDENCY CHAIN (all computed from the same adjustments):")
print("="*70)
for c in report.comps:
    print(f"  Comp#{c.seq} {c.address[:26]:<26} sale ${c.sale_price:>10,.0f} "
          f"net {c.net_pct():>+5.1f}% gross {c.gross_pct():>4.1f}% -> adj ${c.adjusted_price():>10,.0f}")
print(f"\n  CONCLUDED VALUE (weighted, rounded): ${report.valuation.appraised_value:,.0f}")

print("\n" + "="*70)
print("PER-COMP NARRATIVE (generated from those same numbers, Logan's voice):")
print("="*70)
print(per_comp_narrative(report.comps[1], subject, is_most_recent=False))

print("\n" + "="*70)
print("GUIDELINE DISCLOSURE (auto-fires when thresholds exceeded):")
print("="*70)
gd = guideline_disclosure(report.comps)
print(gd if gd else "(no comps exceed guidelines with these placeholder numbers)")

print("\n" + "="*70)
print("WEIGHTING BLOCK (with dependency-chain lint guard):")
print("="*70)
print(weighting_block(report))
