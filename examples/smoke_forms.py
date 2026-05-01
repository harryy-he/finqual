"""
Smoke / exploration script for the :class:`FinqualForms` (Form 4 + 13F) interface.

Not a test. Run with::

    python examples/smoke_forms.py

CIK 0001166559 = Berkshire Hathaway — historically a useful 13F filer.
"""

import finqual as fq

tickers = ["0001166559"]

for ticker in tickers:
    fq_forms = fq.FinqualForms(ticker)
    fq_forms.get_insider_transactions_period("3m").to_pandas()
    fq_forms.get_form_13_period(2).to_pandas()
