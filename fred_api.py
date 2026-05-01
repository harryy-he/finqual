import requests
from datetime import date
import pandas as pd

class FredClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

        self.headers = {
            "Accept": "application/json",
            "User-Agent": "python-client/1.0",
        }

    def get_series(
        self,
        series_id,
        realtime_start=None,
        realtime_end=None,
        observation_start=None,
        observation_end=None,
        units="lin",
        offset=0,
        sort_order="asc",
        file_type="json",
        as_of_date = None,
        return_full_history = False,
    ):

        today = date.today().isoformat()
        as_of_date = as_of_date or today

        # --- Date checks

        if as_of_date is not None:
            if as_of_date > today:
                raise ValueError(f"as_of_date is in future, please adjust so as_of_date is before or equal to {today}")

        if realtime_start is None:
            if return_full_history:
                realtime_start = "1776-07-04"

            else:
                realtime_start = as_of_date or today

        if realtime_end is None:
            realtime_end = as_of_date or today

        if observation_start is None:
            observation_start = "1776-07-04"

        if observation_end is None:
            observation_end = as_of_date or today

        if realtime_start > realtime_end:
            raise ValueError("realtime_start is after realtime_end, please adjust so realtime_start is before or equal to realtime_end")

        if observation_start > observation_end:
            raise ValueError("observation_start is after observation_end, please adjust so observation_start is before or equal to observation_end")

        # --- Queries

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": file_type,

            "realtime_start": realtime_start or today,
            "realtime_end": realtime_end or today,

            "observation_start": observation_start,
            "observation_end": observation_end,

            "units": units,

            "offset": offset,
            "sort_order": sort_order,
        }

        # remove None values (important for API cleanliness)
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(
            self.base_url,
            params=params,
            headers=self.headers,
            timeout=10
        )

        response.raise_for_status()
        return response.json()


if __name__ == '__main__':

    api_key = '79bd13604bbe0db51d65ce6dfdca87fb'

    fred_client = FredClient(api_key)

    observation_start = "2024-01-01"
    as_of_date = "2026-05-01"

    data = fred_client.get_series("GDP", observation_start=observation_start,
                                  as_of_date=as_of_date,
                                  return_full_history=True)
    data