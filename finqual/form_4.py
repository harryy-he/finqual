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
            "TransactionType": "Non-Derivative",
        }
        rows.append(fields)

    df_nonderiv = pl.DataFrame(rows)

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
            "TransactionType": "Derivative",
        }
        rows.append(fields)

    df_concat = pl.DataFrame(rows)

    # ---

    df_concat = df_concat.with_columns([
        pl.col("TransactionCode").replace(TRANSACTION_CODES),
        pl.col("AcquisitionDisposal").replace(ACQUISITION_CODES),
        pl.col("OwnershipType").replace(OWNERSHIP_MAP),
    ])

    return df_concat

