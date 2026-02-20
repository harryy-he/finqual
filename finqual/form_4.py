import xml.etree.ElementTree as ET
import polars as pl
import requests

# ---

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
    "Y": "Other exempt transaction"
}

ACQUISITION_CODES = {
    "A": "Acquisition",
    "D": "Disposal",
}

OWNERSHIP_MAP = {
    "D": "Direct ownership",
    "I": "Indirect ownership"
}


def extract_roles(reporting_owner) -> dict:
    """
    Returns a dictionary of reporting owner types from an XML file
    """
    officer_title = gettext(reporting_owner, ".//officerTitle") or ""

    is_officer = gettext(reporting_owner, ".//isOfficer") == "1"
    is_director = gettext(reporting_owner, ".//isDirector") == "1"
    is_10pct = gettext(reporting_owner, ".//isTenPercentOwner") == "1"
    is_other = gettext(reporting_owner, ".//isOther") == "1"

    is_csuite = is_officer and any(
        k in officer_title.lower() for k in
        ["ceo", "cfo", "coo", "cto", "cio", "cso", "cao", "chief"]
    )

    # Boolean flags
    roles_flags = {
        "CSuite": is_csuite,
        "Officer": is_officer,
        "Director": is_director,
        "10PercentOwner": is_10pct,
        "Other": is_other,
    }

    return roles_flags

# ---
def gettext(parent, path):
    el = parent.find(path)
    return el.text if el is not None else None


def retrieve_form_4(xml_url: str, headers: dict) -> pl.DataFrame:

    resp = requests.get(xml_url, headers=headers)
    resp.raise_for_status()

    # Parse XML
    root = ET.fromstring(resp.content)

    # ---

    rows = []

    for tx in root.findall(".//nonDerivativeTransaction"):
        fields = {
            "Ticker": gettext(root, ".//issuerTradingSymbol"),
            "Security": gettext(tx, ".//securityTitle/value"),
            "Date": gettext(tx, ".//transactionDate/value"),
            "Name": gettext(root, ".//reportingOwnerId/rptOwnerName"),
            "Position": gettext(root, ".//officerTitle"),
            "TransactionCode": gettext(tx,".//transactionCoding/transactionCode"),
            "Shares": gettext(tx, ".//transactionShares/value"),
            "TransactionPrice": gettext(tx,".//transactionPricePerShare/value"),
            "AcquisitionDisposal": gettext(tx,".//transactionAcquiredDisposedCode/value"),
            "SharesOwnedFollowingTransaction": gettext(tx,".//sharesOwnedFollowingTransaction/value"),
            "OwnershipType": gettext(tx, ".//directOrIndirectOwnership/value"),
            "TransactionType": "Non-Derivative Transaction",
        }

        # --- Adding insider transactions
        reporting_owner = root.find(".//reportingOwner")
        role_flags = extract_roles(reporting_owner)
        fields.update(role_flags)

        rows.append(fields)

    # ---

    for tx in root.findall(".//derivativeTransaction"):
        fields = {
            "Ticker": gettext(root, ".//issuerTradingSymbol"),
            "Security": gettext(tx, ".//securityTitle/value"),
            "Date": gettext(tx, ".//transactionDate/value"),
            "Name": gettext(root, ".//reportingOwnerId/rptOwnerName"),
            "Position": gettext(root, ".//officerTitle"),
            "TransactionCode": gettext(tx,".//transactionCoding/transactionCode"),
            "Shares": gettext(tx, ".//transactionShares/value"),
            "TransactionPrice": gettext(tx,".//transactionPricePerShare/value"),
            "AcquisitionDisposal": gettext(tx,".//transactionAcquiredDisposedCode/value"),
            "SharesOwnedFollowingTransaction": gettext(tx,".//sharesOwnedFollowingTransaction/value"),
            "OwnershipType": gettext(tx, ".//directOrIndirectOwnership/value"),
            "TransactionType": "Derivative Transaction",
        }

        # --- Adding insider transactions
        reporting_owner = root.find(".//reportingOwner")
        role_flags = extract_roles(reporting_owner)
        fields.update(role_flags)

        rows.append(fields)

    # ---

    for h in root.findall(".//nonDerivativeHolding"):
        fields = {
            "Ticker": gettext(root, ".//issuerTradingSymbol"),
            "Security": gettext(h, ".//securityTitle/value"),
            "Date": None,
            "Name": gettext(root, ".//reportingOwnerId/rptOwnerName"),
            "Position": gettext(root, ".//officerTitle"),
            "TransactionCode": None,
            "Shares": None,
            "TransactionPrice": None,
            "AcquisitionDisposal": None,
            "SharesOwnedFollowingTransaction": gettext(h, ".//sharesOwnedFollowingTransaction/value"),
            "OwnershipType": gettext(h, ".//directOrIndirectOwnership/value"),
            "NatureOfOwnership": gettext(h, ".//natureOfOwnership/value"),
            "TransactionType": "Non-Derivative Holding",
        }

        rows.append(fields)

    # ---

    for h in root.findall(".//DerivativeHolding"):
        fields = {
            "Ticker": gettext(root, ".//issuerTradingSymbol"),
            "Security": gettext(h, ".//securityTitle/value"),
            "Date": None,
            "Name": gettext(root, ".//reportingOwnerId/rptOwnerName"),
            "Position": gettext(root, ".//officerTitle"),
            "TransactionCode": None,
            "Shares": None,
            "TransactionPrice": None,
            "AcquisitionDisposal": None,
            "SharesOwnedFollowingTransaction": gettext(h, ".//sharesOwnedFollowingTransaction/value"),
            "OwnershipType": gettext(h, ".//directOrIndirectOwnership/value"),
            "NatureOfOwnership": gettext(h, ".//natureOfOwnership/value"),
            "TransactionType": "Derivative Holding",
        }

        rows.append(fields)

    df_concat = pl.DataFrame(rows)

    # ---

    df_concat = df_concat.with_columns([
        pl.col("TransactionCode").replace(TRANSACTION_CODES),
        pl.col("AcquisitionDisposal").replace(ACQUISITION_CODES),
        pl.col("OwnershipType").replace(OWNERSHIP_MAP),
    ])

    # ---

    df_concat = df_concat.select(
        "Ticker", "Security", "Date",
        "Name", "Position",
        "CSuite", "Officer", "Director", "10PercentOwner", "Other",
        "TransactionCode", "Shares", "TransactionPrice",
        "AcquisitionDisposal", "SharesOwnedFollowingTransaction",
        "OwnershipType", "TransactionType",
    )

    return df_concat
