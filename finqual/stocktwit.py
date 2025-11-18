import cloudscraper

class StockTwit:
    """
    Retrieve stock data from StockTwits for one or multiple tickers.

    Attributes
    ----------
    tickers : list[str]
        List of ticker symbols to retrieve data for.
    """

    def __init__(self, tickers: str | list[str]) -> list[str]:
        """
        Initialize the StockTwit instance.

        Parameters
        ----------
        tickers : str | list[str]
            A single ticker symbol as a string or a list of ticker symbols.
        """
        self.tickers = self._load_tickers(tickers)

    @staticmethod
    def _load_tickers(tickers: str | list[str]):
        """
        Normalize input into a list of tickers.

        Parameters
        ----------
        tickers : str | list[str]
            Single ticker as a string or multiple tickers as a list.

        Returns
        -------
        list[str]
            List of ticker symbols.
        """
        if isinstance(tickers, str):
            return [tickers]
        else:
            return tickers

    def retrieve_data(self) -> dict[str, float]:
        """
        Retrieve the previous closing prices for the tickers from StockTwits.

        Returns
        -------
        dict[str, float]
            Dictionary mapping ticker symbols to their last closing price.

        Raises
        ------
        KeyError
            If a ticker is not found in the response.
        """
        tickers_request = ','.join(self.tickers)
        url = 'https://ql.stocktwits.com/batch?symbols=' + tickers_request

        scraper = cloudscraper.create_scraper()
        response = scraper.get(url)
        response = response.json()

        last_prices = {}

        for ticker in self.tickers:
            last_price = response[ticker]['PreviousClose']
            last_prices[ticker] = last_price

        return last_prices

# a = StockTwit(["TSLA"]).retrieve_data()
