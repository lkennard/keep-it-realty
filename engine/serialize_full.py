"""
serialize_full.py — assembles a complete MISMO 2.6 GSE file for TOTAL import.

Wraps the validated comp-grid serializer (serialize_26) with the subject block,
neighborhood/market section, and 1004MC, into the VALUATION_RESPONSE envelope TOTAL reads.

Structure mirrors the real TOTAL export (2767 Uluwehi St):
  VALUATION_RESPONSE > REPORT > FORM(s) > MARKET/SUBJECT_PROJECT
                     > PROPERTY > STRUCTURE/SITE
                     > (SALES_COMPARISON > COMPARABLE(subject) + COMPARABLE_SALE x6)
                     > VALUATION (conclusion)

Adjustments stay BLANK (Logan's judgment). This places facts and computes what's
factual (grid math when adjustments exist, MC stats when dated data exists).
No embedded PDF in this pass — that's the delivery-format concern, not authoring import.
"""
from __future__ import annotations
from xml.sax.saxutils import quoteattr
from .mismo_model import Report
from .serialize_26 import serialize_comparable_sale, _attr
from .market_conditions import MarketConditions

MISMO_HEADER = '<?xml version="1.0" encoding="utf-8"?>'


def _subject_comparable(report: Report) -> str:
    """Subject rendered as COMPARABLE seq 0 (TOTAL's structure)."""
    s = report.subject
    if not s:
        return ""
    return (
        f'<COMPARABLE {_attr("PropertySequenceIdentifier", 0)}>'
        f'<LOCATION {_attr("PropertyStreetAddress", report.subject_address)} '
        f'{_attr("PropertyStreetAddress2", report.subject_city_state_zip)} />'
        f'<ROOM_ADJUSTMENT {_attr("TotalBedroomCount", s.beds)} '
        f'{_attr("TotalBathroomCount", s.baths)} />'
        f'</COMPARABLE>'
    )


def _property_block(report: Report) -> str:
    s = report.subject
    tmk = s.tmk if s else ""
    return (
        f'<PROPERTY {_attr("_StreetAddress", report.subject_address)} '
        f'{_attr("_City", "Koloa")} {_attr("_State", "HI")} {_attr("_PostalCode", "96756")}>'
        f'<_IDENTIFICATION {_attr("AssessorsParcelIdentifier", tmk)} />'
        f'</PROPERTY>'
    )


def _market_block(report: Report, mc: MarketConditions) -> str:
    """Neighborhood + 1004MC market section."""
    return (
        f'<MARKET>'
        f'<SUBJECT_PROJECT '
        f'{_attr("MarketTrendsReconciliationComment", mc.trend_note())} />'
        f'</MARKET>'
    )


def _sales_comparison(report: Report) -> str:
    subj = _subject_comparable(report)
    comps = "".join(serialize_comparable_sale(c) for c in report.comps)
    return f'<SALES_COMPARISON>{subj}{comps}</SALES_COMPARISON>'


def _valuation_block(report: Report) -> str:
    v = report.valuation
    val = v.appraised_value if v else 0
    eff = v.effective_date if v else ""
    return (f'<VALUATION {_attr("PropertyAppraisedValueAmount", val)} '
            f'{_attr("AppraisalEffectiveDate", eff)} />')


def serialize_full_report(report: Report, mc: MarketConditions) -> str:
    """Emit the complete importable MISMO 2.6 GSE file."""
    body = (
        f'<VALUATION_RESPONSE MISMOVersionID="2.6GSE">'
        f'<REPORT {_attr("AppraiserFileIdentifier", report.file_number)}>'
        f'<FORM {_attr("AppraisalReportContentType", report.form_type)}>'
        f'{_market_block(report, mc)}'
        f'</FORM>'
        f'</REPORT>'
        f'{_property_block(report)}'
        f'{_sales_comparison(report)}'
        f'{_valuation_block(report)}'
        f'</VALUATION_RESPONSE>'
    )
    return MISMO_HEADER + "\n" + body
