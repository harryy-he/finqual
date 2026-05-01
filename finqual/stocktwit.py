"""
Thin wrapper around StockTwits' batch quote endpoint.

Returns a ``{ticker: previous_close}`` mapping for one or many tickers.
"""

from __future__ import annotations

from urllib.parse import quote

import cloudscraper

# Public StockTwits batch-quote endpoint.
_STOCKTWITS_BATCH_URL = "https://ql.stocktwits.com/batch"

# Network timeout for HTTP calls (seconds).
_REQUEST_TIMEOUT_SECS = 30


class StockTwit:
    """
    Retrieve previous-close prices from StockTwits for one or multiple tickers.

    Attributes
    ----------
    tickers : list[str]
        Normalised list of ticker symbols.
    """

    def __init__(self, tickers: str | list[str]) -> None:
        """
        Parameters
        ----------
        tickers : str | list[str]
            A single ticker symbol as a string, or a list of ticker symbols.
        """
        self.tickers = self._load_tickers(tickers)

    @staticmethod
    def _load_tickers(tickers: str | list[str]) -> list[str]:
        """Normalise input into a list of tickers."""
        if isinstance(tickers, str):
            return [tickers]
        if not all(isinstance(t, str) for t in tickers):
            raise TypeError("All tickers must be strings.")
        return list(tickers)

    def retrieve_data(self) -> dict[str, float]:
        """
        Retrieve the previous closing prices for the tickers.

        Returns
        -------
        dict[str, float]
            Dictionary mapping ticker → ``PreviousClose``. Tickers absent
            from the response are silently omitted (rather than raising).
        """
        # URL-encode each symbol to defend against unusual characters.
        encoded = ",".join(quote(t, safe="") for t in self.tickers)
        url = f"{_STOCKTWITS_BATCH_URL}?symbols={encoded}"

        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=_REQUEST_TIMEOUT_SECS)
        response.raise_for_status()
        payload = response.json()

        last_prices: dict[str, float] = {}
        for ticker in self.tickers:
            entry = payload.get(ticker)
            if entry is None or "PreviousClose" not in entry:
                continue
            last_prices[ticker] = entry["PreviousClose"]
        return last_prices
