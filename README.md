# Keep It Realty — Appraisal Production Engine

Format-independent core for replicating Logan's appraisal production process.
Scope boundary is sacred: the tool assembles, grades, drafts, and computes AROUND
Logan's judgment. It never selects final comps, sets adjustments, or concludes value.

## Pipeline
    HIS CSV (today) / VOW RESO API (later)  →  his_parse  →  normalized Comps
       →  grade  →  ranked+annotated candidates  →  [LOGAN SELECTS]
       →  adjustments (Logan sets)  →  dependency engine (recompute+propagate)
       →  narrative drafter  →  paste-ready text + TOTAL-import file

## Modules
- `engine/his_parse.py` — HIS one-line CSV → normalized Comp/Subject. Shared input
  layer; the VOW API adapter will emit the same Comp objects.
- `engine/grade.py` — comp grading/ranking. Encodes the rare-subject selection logic.

## Encoded selection patterns (captured live from the Poipu Aina file, 2026-07-17)
1. Physical-comparability-first expansion (GLA+lot can outrank geographic proximity
   for rare subjects).
2. Amenity contamination is a separate exclusion axis from distance.
3. Buyer-segment logic: the competing set is who would cross-shop the subject.
4. DOM-0 / cash = scrutinize-not-exclude; scrutiny is lighter at high price tiers.
5. Per-axis bracketing; guideline exceedances flagged for disclosure.

## Still open (not built)
- Dependency-chain engine (adjustments → propagated value everywhere).
- Narrative drafter (standing notes + per-comp narratives in Logan's voice).
- TOTAL import: target MISMO 3.6 (published schema). De-risk by exporting one
  finished report to XML from TOTAL and reverse-engineering the known-good file.
- VOW RESO API adapter (pending HIS feed subscription; TMK-queryability to confirm).

## XML generation (added 2026-07-17)
- `engine/mismo_model.py` — version-independent valuation model (comps, adjustments,
  dependency-chain math). Knows nothing about 2.6 vs 3.6.
- `engine/serialize_26.py` — MISMO 2.6 GSE serializer, reverse-engineered from a real
  TOTAL export. Emits TOTAL-importable COMPARABLE_SALE blocks.
- `tests_validate_xml.py` — proves the serializer reproduces TOTAL's exact output:
  net adj, adjusted price, net/gross %, $/GLA all match to the penny vs the real
  2767 Uluwehi file.

### Version-swap plan (Logan's call, 2026-07-17)
Build 2.6 now (live standard until Nov 2026), swap to 3.6 later as `serialize_36.py`.
Model + engine + grading are unchanged by the swap — only the serializer is new.

## Still open
- Full-report serialization (subject block, neighborhood, cost approach, 1004MC wiring).
- Embedded PDF (base64) — the one genuinely hard sub-problem; may be optional for a
  data-populating import into a fresh report.
- Narrative drafter (standing notes + per-comp narratives in Logan's voice).
- Round-trip test: generate a full file, import into TOTAL, confirm clean ingestion.

## Narrative engine + live assignment (added 2026-07-17)
- `engine/narrative.py` — per-comp narratives, guideline-exceedance disclosure, and
  weighting block in Logan's voice, generated FROM Logan's adjustments. Grid and prose
  cannot drift — both derive from one source. Includes a dependency-chain lint guard.
- `assignment_poipu_aina.py` — live assignment: subject + 6 selected comps as data,
  adjustment amounts + weights BLANK for Logan to set.
- `demo_pipeline.py` — end-to-end proof (placeholder numbers): adjustments -> net/gross %,
  adjusted prices, disclosure, narrative, weighting, all from one source.

## How Logan uses it (current backend flow)
1. Fill adjustment `amount=` fields + `weights` in assignment_poipu_aina.py (his judgment).
2. Run the pipeline -> narratives + dependency-chain math + importable MISMO comp grid.
3. (Coming) full-report serializer emits the complete importable file.
4. Import to TOTAL, add maps/photos/pages/commentary, sign, deliver.

## Roadmap
- [next] Full-report serializer (subject/site/structure/1004MC/valuation wrapper).
- [next] Round-trip test: generate full file -> import into TOTAL -> confirm ingestion.
- Web UI (Next.js) where adjustments/weights are entered and narratives regenerate live.
- Supabase persistence; VOW RESO API adapter (replaces manual CSV) when feed subscribed.
- serialize_36.py when UAD 3.6 lands (Nov 2026) — model/engine unchanged.

## Full-report build command (added 2026-07-17)
- `build_report.py` — THE COMMAND. Run `python3 build_report.py` to generate the
  MISMO import file + paste-ready narratives for an assignment.
- `engine/serialize_full.py` — assembles the complete MISMO 2.6 file (subject block,
  market section, comp grid, valuation) in the VALUATION_RESPONSE envelope TOTAL reads.
- `engine/market_conditions.py` — 1004MC engine, built to Fannie/forum best practice:
  subject's competing SEGMENT (not whole neighborhood), time-bucketed, thin buckets
  DISCLOSED not invented. Requires a dated MLS pull (one-line export lacks sale dates).

### Output (per run, in output/)
- `Poipu_Aina.xml` — the MISMO file to import into TOTAL (well-formed, 6 comps placed)
- `Poipu_Aina_narratives.txt` — per-comp narratives, guideline disclosure, weighting, MC note

### To finish this report
1. Verify subject GLA (assumed 4,532).
2. Set adjustments + weights in assignment_poipu_aina.py (your judgment).
3. Provide a dated neighborhood-segment MLS pull for the 1004MC.
4. Re-run `python3 build_report.py`.
5. Import Poipu_Aina.xml into TOTAL; add maps/photos/sketch/signature; deliver.

### Known next gates
- Real round-trip: import the generated XML into TOTAL, confirm clean ingestion, tune
  fields to match TOTAL's exact expectations (this is the validation we haven't crossed).
- The generated file omits the embedded PDF (delivery format), which authoring-import
  may not require — confirm during the round-trip test.

## Dated export + real 1004MC (added 2026-07-17)
- Parser now reads the richer HIS export with `Sold Date`, `Agent Remarks`, `Public Remarks`.
- `engine/enrich.py` — remarks keyword scanner (pool/ADU/solar/ocean view/etc., visible
  aids for comp selection, NOT auto-adjustments) + MC-record builder (segment-filtered).
- `build_report.py` computes the real 1004MC when a dated pull is at `data/neighborhood_dated.csv`.
- Verified on real data: 45 dated solds in the competing segment produced live absorption,
  median-price, and median-DOM buckets. Appraiser concludes the trend direction.

### To refresh the 1004MC
Drop a dated HIS export (with a Sold Date column) at `data/neighborhood_dated.csv`, re-run build.
