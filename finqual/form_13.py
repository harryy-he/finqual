import requests
import xml.etree.ElementTree as ET
import polars as pl

# 13F information table namespace
SEC_13F_NS = {"ns": "http://www.sec.gov/edgar/document/thirteenf/informationtable"}

def gettext(el, path):
    node = el.find(path, SEC_13F_NS)
    return node.text if node is not None else None

def retrieve_form_13f_aggregated(xml_url: str, headers: dict) -> pl.DataFrame:
    """
    Retrieve and parse a 13F infoTable XML
    and aggregate holdings by issuer (CUSIP-level).
    """

    resp = requests.get(xml_url, headers=headers)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)

    rows = []

    for holding in root.findall(".//ns:infoTable", SEC_13F_NS):
        # Extract the numeric shares text
        shares_text = gettext(holding, "ns:shrsOrPrnAmt/ns:sshPrnamt")
        value_text = gettext(holding, "ns:value")

        rows.append({
            "CUSIP": gettext(holding, "ns:cusip"),
            "Issuer": gettext(holding, "ns:nameOfIssuer"),
            "TitleOfClass": gettext(holding, "ns:titleOfClass"),
            "Shares": float(shares_text) if shares_text else 0.0,
            "Value_USD": float(value_text) * 1000 if value_text else 0.0,
        })

    df = pl.DataFrame(rows)

    df_agg = (
        df.group_by(["CUSIP", "Issuer", "TitleOfClass"])
        .agg([
            pl.sum("Shares").alias("TotalShares"),
            pl.sum("Value_USD").alias("TotalValue_USD"),
        ])
        .sort("TotalValue_USD", descending=True)
    )

    # Optionally, portfolio weight:
    df_agg = df_agg.with_columns(
        (pl.col("TotalValue_USD") / pl.sum("TotalValue_USD")).alias("PortfolioWeight")
    )

    return df_agg