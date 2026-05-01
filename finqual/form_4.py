"""
Parsing of SEC Form 4 (statement of changes in beneficial ownership) XML filings.

Returns a flat ``polars.DataFrame`` with one row per non-derivative or
derivative transaction or holding, decorated with role flags for the
reporting owner (officer, director, ten-percent owner, C-suite, etc.).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Mapping, Optional

import polars as pl

from finqual.sec_edgar.xml_utils import gettext, safe_get_xml

# ------------------------------------------------------------------ #
# Lookup tables (SEC documentation)
# ------------------------------------------------------------------ #

TRANSACTION_CODES = {
    "P": "Open market purchase",
    "S": "Open market sale",
    "A": "Grant or award from issuer",
    "D": "Disposition to issuer",
    "F": "Tax/exercise payment with shares",
    "I": "Discretionary trustee transaction",
    "M": "Option/derivative exercise or conversion",
    "X": "Option exercise (exempt/cashless)",
    "G": "Gift",
    "L": "Small acquisition",
    "W": "Inheritance",
    "Z": "Voting trust transaction",
    "J": "Other adjustment",
    "K": "Equity swap/hedge",
    "O": "Out-of-money derivative exercise",
    "U": "Tender of shares",
    "V": "Voluntary report",
    "Y": "Other exempt transaction",
}

ACQUISITION_CODES = {
    "A": "Acquisition",
    "D": "Disposal",
}

OWNERSHIP_MAP = {
    "D": "Direct ownership",
    "I": "Indirect ownership",
}

# Keywords that escalate an "Officer" reporter to "C-Suite" within :func:`extract_roles`.
_CSUITE_KEYWORDS = ("ceo", "cfo", "coo", "cto", "cio", "cso", "cao", "chief")

# Final column order returned by :func:`retrieve_form_4`.
_OUTPUT_COLUMNS = (
    "Ticker",
    "Security",
    "Date",
    "Name",
    "Position",
    "CSuite",
    "Officer",
    "Director",
    "10PercentOwner",
    "Other",
    "TransactionCode",
    "Shares",
    "TransactionPrice",
    "AcquisitionDisposal",
    "SharesOwnedFollowingTransaction",
    "OwnershipType",
    "NatureOfOwnership",
    "TransactionType",
)


def extract_roles(reporting_owner: Optional[ET.Element]) -> dict:
    """
    Extract role flags from a ``<reportingOwner>`` element.

    Returns a dictionary with boolean flags for ``Officer``, ``Director``,
    ``10PercentOwner``, ``Other`` and a derived ``CSuite`` flag based on
    common officer-title keywords (CEO/CFO/COO/...).
    """
    if reporting_owner is None:
        return {
            "CSuite": False,
            "Officer": False,
            "Director": False,
            "10PercentOwner": False,
            "Other": False,
        }

    officer_title = (gettext(reporting_owner, ".//officerTitle") or "").lower()
    is_officer = gettext(reporting_owner, ".//isOfficer") == "1"
    is_director = gettext(reporting_owner, ".//isDirector") == "1"
    is_10pct = gettext(reporting_owner, ".//isTenPercentOwner") == "1"
    is_other = gettext(reporting_owner, ".//isOther") == "1"

    is_csuite = is_officer and any(k in officer_title for k in _CSUITE_KEYWORDS)

    return {
        "CSuite": is_csuite,
        "Officer": is_officer,
        "Director": is_director,
        "10PercentOwner": is_10pct,
        "Other": is_other,
    }


# ------------------------------------------------------------------ #
# Row builder (used for both transactions and holdings, derivative or not)
# ------------------------------------------------------------------ #

def _build_row(
    el: ET.Element,
    root: ET.Element,
    *,
    transaction_type: str,
    is_holding: bool,
) -> dict:
    """
    Construct the canonical Form-4 row from a transaction/holding element.

    A *holding* never has a transaction date, code, share count, price or
    acquisition/disposal flag, so those fields are forced to ``None``.
    """
    if is_holding:
        date = None
        tx_code = None
        shares = None
        price = None
        ack_disp = None
    else:
        date = gettext(el, ".//transactionDate/value")
        tx_code = gettext(el, ".//transactionCoding/transactionCode")
        shares = gettext(el, ".//transactionShares/value")
        price = gettext(el, ".//transactionPricePerShare/value")
        ack_disp = gettext(el, ".//transactionAcquiredDisposedCode/value")

    return {
        "Ticker": gettext(root, ".//issuerTradingSymbol"),
        "Security": gettext(el, ".//securityTitle/value"),
        "Date": date,
        "Name": gettext(root, ".//reportingOwnerId/rptOwnerName"),
        "Position": gettext(root, ".//officerTitle"),
        "TransactionCode": tx_code,
        "Shares": shares,
        "TransactionPrice": price,
        "AcquisitionDisposal": ack_disp,
        "SharesOwnedFollowingTransaction": gettext(el, ".//sharesOwnedFollowingTransaction/value"),
        "OwnershipType": gettext(el, ".//directOrIndirectOwnership/value"),
        "NatureOfOwnership": gettext(el, ".//natureOfOwnership/value"),
        "TransactionType": transaction_type,
    }


# ------------------------------------------------------------------ #
# Public entry point
# ------------------------------------------------------------------ #

def retrieve_form_4(xml_url: str, headers: Mapping[str, str]) -> pl.DataFrame:
    """
    Download and parse a single Form 4 XML filing into a Polars DataFrame.

    Parameters
    ----------
    xml_url : str
        URL pointing to the Form 4 ``.xml`` document.
    headers : Mapping[str, str]
        HTTP headers (typically :data:`finqual.config.headers.sec_headers`).

    Returns
    -------
    polars.DataFrame
        Rows for every non-derivative / derivative transaction and holding,
        decorated with reporter-role flags.
    """
    root = safe_get_xml(xml_url, headers)
    reporting_owner = root.find(".//reportingOwner")
    role_flags = extract_roles(reporting_owner)

    # Mapping of XPath → (transaction_type, is_holding)
    sources = (
        (".//nonDerivativeTransaction", "Non-Derivative Transaction", False),
        (".//derivativeTransaction", "Derivative Transaction", False),
        (".//nonDerivativeHolding", "Non-Derivative Holding", True),
        # NB: SEC schema uses lowercase 'd' — the previous "DerivativeHolding"
        # never matched and silently dropped these rows.
        (".//derivativeHolding", "Derivative Holding", True),
    )

    rows: list[dict] = []
    for xpath, transaction_type, is_holding in sources:
        for el in root.findall(xpath):
            row = _build_row(el, root, transaction_type=transaction_type, is_holding=is_holding)
            # Roles are reporter-level metadata — apply to every row.
            row.update(role_flags)
            rows.append(row)

    if not rows:
        return pl.DataFrame(schema={col: pl.Utf8 for col in _OUTPUT_COLUMNS})

    df = pl.DataFrame(rows)

    df = df.with_columns(
        [
            pl.col("TransactionCode").replace(TRANSACTION_CODES),
            pl.col("AcquisitionDisposal").replace(ACQUISITION_CODES),
            pl.col("OwnershipType").replace(OWNERSHIP_MAP),
        ]
    )

    return df.select(list(_OUTPUT_COLUMNS))
