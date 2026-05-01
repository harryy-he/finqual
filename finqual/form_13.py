"""
Parsing of SEC Form 13F-HR institutional-holdings XML filings.

Aggregates holdings by issuer + asset-type and computes portfolio weights.
"""

from __future__ import annotations

from typing import Mapping

import polars as pl

from finqual.sec_edgar.xml_utils import gettext, safe_get_xml

# 13F information-table namespace
SEC_13F_NS = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}

# 13F values are reported in **thousands of USD** historically; we normalise to whole dollars.
# (Note: post-2023 some filers began reporting actual dollars – callers needing strict
# accuracy should verify by sampling against the underlying filing.)
SEC_13F_VALUE_MULTIPLIER = 1000.0


def retrieve_form_13f_aggregated(xml_url: str, headers: Mapping[str, str]) -> pl.DataFrame:
    """
    Retrieve and parse a 13F ``infoTable`` XML and aggregate holdings.

    Holdings are grouped by ``(CUSIP, Issuer, TitleOfClass, AssetType)`` —
    ``AssetType`` distinguishes Equity / Put / Call so option overlays are
    not collapsed into the underlying.

    Parameters
    ----------
    xml_url : str
        URL of the 13F holdings XML (``infoTable``).
    headers : Mapping[str, str]
        HTTP headers (typically :data:`finqual.config.headers.sec_headers`).

    Returns
    -------
    polars.DataFrame
        Aggregated holdings with ``TotalShares``, ``TotalValue_USD`` and
        ``PortfolioWeight`` columns, sorted by total value descending.
    """
    root = safe_get_xml(xml_url, headers)

    rows: list[dict] = []
    for holding in root.findall(".//ns:infoTable", SEC_13F_NS):
        shares_text = gettext(holding, "ns:shrsOrPrnAmt/ns:sshPrnamt", SEC_13F_NS)
        value_text = gettext(holding, "ns:value", SEC_13F_NS)
        put_call = gettext(holding, "ns:putCall", SEC_13F_NS)

        asset_type = put_call.capitalize() if put_call else "Equity"

        rows.append(
            {
                "CUSIP": gettext(holding, "ns:cusip", SEC_13F_NS),
                "Issuer": gettext(holding, "ns:nameOfIssuer", SEC_13F_NS),
                "TitleOfClass": gettext(holding, "ns:titleOfClass", SEC_13F_NS),
                "AssetType": asset_type,
                "Shares": float(shares_text) if shares_text else 0.0,
                "Value_USD": float(value_text) * SEC_13F_VALUE_MULTIPLIER if value_text else 0.0,
            }
        )

    if not rows:
        return pl.DataFrame()

    df = pl.DataFrame(rows)

    df_agg = (
        df.group_by(["CUSIP", "Issuer", "TitleOfClass", "AssetType"])
        .agg(
            [
                pl.sum("Shares").alias("TotalShares"),
                pl.sum("Value_USD").alias("TotalValue_USD"),
            ]
        )
        .sort("TotalValue_USD", descending=True)
    )

    df_agg = df_agg.with_columns(
        (pl.col("TotalValue_USD") / pl.sum("TotalValue_USD")).alias("PortfolioWeight")
    )

    return df_agg
