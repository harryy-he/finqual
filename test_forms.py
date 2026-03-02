import finqual as fq

tickers = ["0001166559"]  # You can add more tickers if needed

for ticker in tickers:

    fq_forms = fq.FinqualForms(ticker)

    df_insider = fq_forms.get_insider_transactions_period("3m").to_pandas()
    df_form13 = fq_forms.get_form_13_period(2).to_pandas()
