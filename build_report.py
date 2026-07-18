#!/usr/bin/env python3
"""
build_report.py — THE COMMAND. Generates the MISMO import file for an assignment.

Usage:
    python3 build_report.py

Produces:
    output/Poipu_Aina.xml   — the MISMO 2.6 file to import into TOTAL
    output/Poipu_Aina_narratives.txt — the narratives to paste into addenda

What it fills:
    - Comp grid: the 6 comps placed with real facts (adjustments blank = your judgment)
    - Grid math: computed IF adjustments are set, else blank
    - Narratives: per-comp + guideline disclosure + weighting, in your voice
    - 1004MC: computed IF a dated neighborhood pull is provided, else flagged
    - Neighborhood: from the segment stats

What stays yours:
    - Adjustment amounts, weights, value conclusion (enter in assignment_poipu_aina.py)
    - Subject GLA verification
    - Maps, photos, sketch, signature (added in TOTAL)
"""
import os
from datetime import date
from assignment_poipu_aina import report, subject
from engine.serialize_full import serialize_full_report
from engine.market_conditions import build_market_conditions, MCRecord
from engine.narrative import per_comp_narrative, guideline_disclosure, weighting_block

OUT = "output"
os.makedirs(OUT, exist_ok=True)

# --- 1004MC: computed from a DATED neighborhood-segment pull if provided. ---
# Point this at a dated HIS export (with a "Sold Date" column). If the file is absent
# or lacks dates, the engine flags it rather than inventing trends.
from engine.his_parse import parse_his_csv
from engine.enrich import to_mc_records

MC_CSV = "data/neighborhood_dated.csv"   # drop a dated segment pull here
SEG_GLA_MIN = 2500                        # subject's competing segment threshold

mc_records: list[MCRecord] = []
try:
    neighborhood = parse_his_csv(MC_CSV)
    mc_records = to_mc_records(neighborhood, gla_min=SEG_GLA_MIN, fee_simple_only=True)
except FileNotFoundError:
    pass  # no dated pull yet -> engine emits the "awaiting dated pull" flag

mc = build_market_conditions(mc_records, as_of=date(2026, 7, 17),
                             segment_description=f"large-lot custom homes, Poipu/Koloa, GLA {SEG_GLA_MIN:,}+ sf, Fee Simple")

# --- Generate the MISMO file ---
xml = serialize_full_report(report, mc)
xml_path = os.path.join(OUT, "Poipu_Aina.xml")
with open(xml_path, "w", encoding="utf-8") as f:
    f.write(xml)

# --- Generate narratives (paste-ready) ---
narr_lines = ["=== PER-COMP NARRATIVES ===\n"]
any_adj = any(a.amount for c in report.comps for a in c.adjustments)
for c in report.comps:
    narr_lines.append(per_comp_narrative(c, subject))
    narr_lines.append("")
narr_lines.append("\n=== GUIDELINE DISCLOSURE ===\n")
gd = guideline_disclosure(report.comps)
narr_lines.append(gd if gd else "(No guideline exceedances — or adjustments not yet set.)")
narr_lines.append("\n=== WEIGHTING BLOCK ===\n")
narr_lines.append(weighting_block(report))
narr_lines.append("\n=== 1004MC MARKET CONDITIONS ===\n")
narr_lines.append(mc.trend_note())

narr_path = os.path.join(OUT, "Poipu_Aina_narratives.txt")
with open(narr_path, "w", encoding="utf-8") as f:
    f.write("\n".join(narr_lines))

# --- Report to console ---
print("=" * 64)
print("BUILD COMPLETE")
print("=" * 64)
print(f"  MISMO file:  {xml_path}  ({len(xml):,} bytes)")
print(f"  Narratives:  {narr_path}")
print()
print(f"  Comps placed: {len(report.comps)}")
print(f"  Adjustments set: {'YES' if any_adj else 'NO — blank, awaiting your judgment'}")
print(f"  1004MC: {'computed' if mc.has_dates else 'awaiting dated MLS pull'}")
print(f"  Value: {'$'+format(report.valuation.appraised_value, ',') if report.valuation and report.valuation.appraised_value else 'not yet reconciled'}")
print()
print("  NEXT: set adjustments + weights in assignment_poipu_aina.py, verify subject GLA,")
print("  provide a dated neighborhood pull for the 1004MC, then re-run this command.")
