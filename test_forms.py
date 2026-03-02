import finqual as fq

tickers = ["0001649339", "0001536411"]  # You can add more tickers if needed

for ticker in tickers:

    fq_forms = fq.FinqualForms(ticker)

    df_insider = fq_forms.get_insider_transactions_period("3m").to_pandas()
    df_form13_period = fq_forms.get_form_13_period(10).to_pandas()
