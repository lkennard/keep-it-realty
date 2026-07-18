"""
serialize_26.py — MISMO 2.6 GSE serializer.

Renders the version-independent mismo_model into the exact 2.6GSE structure TOTAL
emits and imports (reverse-engineered from a real TOTAL export, 2767 Uluwehi St,
AppraisalSoftwareProductVersionIdentifier 6.324).

When 3.6 lands (Nov 2026), a serialize_36.py sits beside this file; the model and
engine do not change. That's the whole point of the split.

This module renders the COMPARABLE_SALE blocks — the comp grid — which is the piece
the engine produces. Full-report assembly (subject, neighborhood, cost, embedded PDF)
is a later brick; this proves the core grid round-trips correctly.
"""
from __future__ import annotations
from xml.sax.saxutils import escape, quoteattr
from .mismo_model import CompSale, Adjustment

UAD_ORG = "UNIFORM APPRAISAL DATASET"


def _attr(name: str, value) -> str:
    """Render one attribute. None/empty -> empty string value, matching TOTAL
    (TOTAL emits _Amount="" for a blank adjustment, not a missing attribute)."""
    if value is None:
        value = ""
    return f'{name}={quoteattr(str(value))}'


def _ext_section(inner: str, tag_prefix: str) -> str:
    """Wrap content in the UAD extension-section boilerplate TOTAL uses everywhere."""
    return (
        f'<{tag_prefix}_EXTENSION>'
        f'<{tag_prefix}_EXTENSION_SECTION ExtensionSectionOrganizationName={quoteattr(UAD_ORG)}>'
        f'<{tag_prefix}_EXTENSION_SECTION_DATA>'
        f'{inner}'
        f'</{tag_prefix}_EXTENSION_SECTION_DATA>'
        f'</{tag_prefix}_EXTENSION_SECTION>'
        f'</{tag_prefix}_EXTENSION>'
    )


def _sale_price_adjustment(a: Adjustment) -> str:
    if a.kind == "Other":
        parts = [_attr("_Type", "Other")]
        if a.other_label is not None:
            parts.append(_attr("_TypeOtherDescription", a.other_label))
        parts.append(_attr("_Amount", a.amount))
        return f'<SALE_PRICE_ADJUSTMENT {" ".join(parts)} />'
    parts = [_attr("_Type", a.kind)]
    if a.description != "":
        parts.append(_attr("_Description", a.description))
    parts.append(_attr("_Amount", a.amount))
    return f'<SALE_PRICE_ADJUSTMENT {" ".join(parts)} />'


def serialize_comparable_sale(c: CompSale) -> str:
    """Render one COMPARABLE_SALE block matching TOTAL's 2.6GSE output."""
    adj_price = c.adjusted_price()
    net = c.net_adjustment()

    header = (
        f'<COMPARABLE_SALE '
        f'{_attr("PropertySequenceIdentifier", c.seq)} '
        f'{_attr("PropertySalesAmount", c.sale_price)} '
        f'{_attr("SalesPricePerGrossLivingAreaAmount", c.price_per_gla())} '
        f'{_attr("DataSourceDescription", f"HIMLS #{c.mls_number};DOM {c.dom}" if c.mls_number else "")} '
        f'{_attr("DataSourceVerificationDescription", c.data_source_verification)} '
        f'{_attr("SalesPriceTotalAdjustmentPositiveIndicator", "Y" if net >= 0 else "N")} '
        f'{_attr("SalePriceTotalAdjustmentAmount", abs(net))} '
        f'{_attr("AdjustedSalesPriceAmount", adj_price)} '
        f'{_attr("SalesPriceTotalAdjustmentGrossPercent", c.gross_pct())} '
        f'{_attr("SalePriceTotalAdjustmentNetPercent", c.net_pct())}>'
    )

    location = (
        f'<LOCATION '
        f'{_attr("LatitudeNumber", c.latitude)} '
        f'{_attr("LongitudeNumber", c.longitude)} '
        f'{_attr("PropertyStreetAddress", c.address)} '
        f'{_attr("PropertyStreetAddress2", c.city_state_zip)} '
        f'{_attr("ProximityToSubjectDescription", c.proximity)} />'
    )

    rooms = (
        f'<ROOM_ADJUSTMENT '
        f'{_attr("TotalRoomCount", c.total_rooms)} '
        f'{_attr("TotalBedroomCount", c.beds)} '
        f'{_attr("TotalBathroomCount", c.baths)} '
        f'{_attr("RoomAdjustmentAmount", "")} />'
    )

    adjustments = "".join(_sale_price_adjustment(a) for a in c.adjustments)

    other_feats = ""
    for i, of in enumerate(c.other_features, start=1):
        other_feats += (
            f'<OTHER_FEATURE_ADJUSTMENT '
            f'{_attr("PropertyFeatureSequenceIdentifier", i)} '
            f'{_attr("PropertyFeatureDescription", of.description or of.other_label)} '
            f'{_attr("PropertyFeatureAdjustmentAmount", of.amount)} />'
        )

    # UAD comparison-detail extension (the GSE-coded facts)
    comp_detail = _ext_section(
        f'<COMPARISON_DETAIL '
        f'{_attr("GSEDataSourceDescription", f"HIMLS #{c.mls_number}")} '
        f'{_attr("GSEDaysOnMarketDescription", c.dom)} '
        f'{_attr("GSESaleType", c.sale_type)} '
        f'{_attr("GSEFinancingType", c.financing)} '
        f'{_attr("GSEListingStatusType", "SettledSale")} '
        f'{_attr("GSEQualityOfConstructionRatingType", c.quality)} '
        f'{_attr("GSEOverallConditionType", c.condition)} />',
        "COMPARISON_DETAIL",
    )

    view_rating = _ext_section(
        f'<COMPARISON_VIEW_OVERALL_RATING {_attr("GSEViewOverallRatingType", c.view_rating)} />',
        "COMPARISON_VIEW_OVERALL_RATING",
    )
    loc_rating = _ext_section(
        f'<COMPARISON_LOCATION_OVERALL_RATING {_attr("GSEOverallLocationRatingType", c.location_rating)} />',
        "COMPARISON_LOCATION_OVERALL_RATING",
    )

    return (
        header + location + rooms + adjustments + other_feats
        + comp_detail + view_rating + loc_rating
        + "</COMPARABLE_SALE>"
    )
