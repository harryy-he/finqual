import cloudscraper

class StockTwit:

    def __init__(self, tickers: str | list[str]):
        self.tickers = self._load_tickers(tickers)

    @staticmethod
    def _load_tickers(tickers: str | list[str]):
        if isinstance(tickers, str):
            return [tickers]
        else:
            return tickers

    def retrieve_data(self):

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
