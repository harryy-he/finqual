class IdCodeNotFoundError(ValueError):
    def __init__(self, ticker_or_cik: str):
        message = f"Could not find items for {ticker_or_cik}"
        super().__init__(message)