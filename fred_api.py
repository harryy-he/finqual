import requests
from datetime import datetime, timezone
import pandas as pd


class FredClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "python-client/1.0",
        }

    # https://api.stlouisfed.org/fred/series/observations?series_id=GDP&api_key=79bd13604bbe0db51d65ce6dfdca87fb
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
        as_of_date=None,
        return_full_history=False,
    ):
        today = datetime.now(timezone.utc).date().isoformat()
        as_of_date = as_of_date or today

        if as_of_date > today:
            raise ValueError(
                f"as_of_date is in future, please adjust so as_of_date is before or equal to {today}"
            )

        if realtime_start is None:
            realtime_start = "1776-07-04" if return_full_history else (as_of_date or today)

        if realtime_end is None:
            realtime_end = as_of_date or today

        if observation_start is None:
            observation_start = "1776-07-04"

        if observation_end is None:
            observation_end = as_of_date or today

        if realtime_start > realtime_end:
            raise ValueError("realtime_start is after realtime_end")

        if observation_start > observation_end:
            raise ValueError("observation_start is after observation_end")

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": file_type,
            "realtime_start": realtime_start,
            "realtime_end": realtime_end,
            "observation_start": observation_start,
            "observation_end": observation_end,
            "units": units,
            "offset": offset,
            "sort_order": sort_order,
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
        response.raise_for_status()

        json_response = response.json()
        df = pd.DataFrame(json_response["observations"])

        return df

    def get_ml_series(self, series_id, start_date, end_date, frequency="monthly", method="point-in-time"):
        # 1. Fetch history
        df = self.get_series(series_id, observation_start="1776-07-04", return_full_history=True)

        # Standardize types and clean dates to yyyy-mm-dd
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['realtime_start'] = pd.to_datetime(df['realtime_start']).dt.normalize()
        df['realtime_end'] = pd.to_datetime(df['realtime_end']).dt.normalize()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # 2. Calculate Revision Numbers
        # For every unique observation date, rank the releases by their start time
        df = df.sort_values(['date', 'realtime_start'])
        df['revision_number'] = df.groupby('date').cumcount() + 1

        # Map frequency string to pandas Offset Alias
        freq_map = {"daily": "D", "monthly": "MS", "quarterly": "QS", "annual": "YS"}
        pd_freq = freq_map.get(frequency.lower(), frequency)

        # Create the target timeline
        timeline = pd.date_range(start=start_date, end=end_date, freq=pd_freq).normalize()
        ml_results = []

        for as_of in timeline:
            if method == "point-in-time":
                # What was known to the world EXACTLY on this calendar date?
                valid_at_time = df[(df['realtime_start'] <= as_of) & (df['realtime_end'] >= as_of)]
                if not valid_at_time.empty:
                    # Get the most recent observation period available at this moment
                    match = valid_at_time.sort_values('date', ascending=False).iloc[0]
                else:
                    match = None

            elif method == "latest":
                # Standardize end_date for "latest" logic
                as_of_end = pd.to_datetime(end_date).normalize()

                # Look for the values where as_of_end is in the valid time period i.e. after realtime_start
                valid_by_end = df[df['realtime_start'] <= as_of_end]

                # Find observations where the date is on or before our end_date
                valid_obs = valid_by_end[valid_by_end['date'] <= as_of]
                if not valid_obs.empty:
                    # Get the latest revision of the most recent observation period
                    match = valid_obs.sort_values(['date', 'realtime_start'], ascending=[False, False]).iloc[0]
                else:
                    match = None

            elif method == "first":

                # Filter for observations that had their first release on or before this calendar date
                valid_obs = df[df['realtime_start'] <= as_of]
                if not valid_obs.empty:
                    # Group by observation date, get the first revision of each,
                    # then pick the most recent observation date among those
                    first_releases = valid_obs.sort_values(['date', 'realtime_start']).groupby(
                        'date').first().reset_index()
                    match = first_releases.sort_values('date', ascending=False).iloc[0]
                else:
                    match = None

            # Append results in a consistent format
            if match is not None:
                ml_results.append({
                    'date': as_of,
                    'value': match['value'],
                    'observation_date': match['date'],
                    'revision_number': match['revision_number']
                })
            else:
                ml_results.append({
                    'date': as_of,
                    'value': None,
                    'observation_date': None,
                    'revision_number': None
                })

        result_df = pd.DataFrame(ml_results)

        # Final formatting: Ensure the 'date' column is just YYYY-MM-DD strings
        result_df['date'] = result_df['date'].dt.strftime('%Y-%m-%d')
        result_df['observation_date'] = result_df['observation_date'].dt.strftime('%Y-%m-%d')

        return result_df[['date', 'value', 'observation_date', 'revision_number']]

    def get_gdp_surprise_series(self, start_date, end_date):
        # 1. Fetch the data (daily frequencies)
        # actual_df: The official BEA value known to the market on each calendar date
        actual_df = self.get_ml_series("A191RL1Q225SBEA", start_date, end_date, frequency="daily", method="first")
        # nowcast_df: The STLENI forecast known to the market on each calendar date
        nowcast_df = self.get_ml_series("STLENI", start_date, end_date, frequency="daily", method="point-in-time")

        # 2. Merge them!
        # CRITICAL: We join on 'date' (calendar time) to see what was known,
        # BUT we must ensure we compare values referring to the SAME quarter.
        df = pd.merge(actual_df, nowcast_df, on='date', suffixes=('_act', '_now'))

        # 3. Identify the "Surprise Trigger"
        # A surprise happens when the market gets a new official observation_date
        # for the actual GDP series.
        df['is_release_day'] = df['observation_date_act'] != df['observation_date_act'].shift(1)

        # 4. Calculate the Surprise with Alignment Check
        # We only care about the Nowcast value that matches the Actual's observation date.
        def calculate_aligned_surprise(row):
            if row['is_release_day']:
                # Does the Nowcast we had today refer to the quarter just released?
                # On release day, STLENI for that quarter is 'finalized'.
                if row['observation_date_act'] == row['observation_date_now']:
                    return row['value_act'] - row['value_now']
                else:
                    # If they don't align, we need to find the Nowcast value
                    # that DID refer to observation_date_act.
                    return 0.0  # Or implement a secondary lookup logic
            return 0.0

        df['gdp_surprise'] = df.apply(calculate_aligned_surprise, axis=1)

        return df


if __name__ == "__main__":
    api_key = "79bd13604bbe0db51d65ce6dfdca87fb"
    client = FredClient(api_key)

    observation_start = "2024-01-01"
    as_of_date = "2026-05-04"

    # data = client.get_series("GDP", observation_start=observation_start,
    #                               as_of_date=as_of_date,
    #                               return_full_history=True)
    #
    # ml_data = client.get_ml_series(
    #     series_id="A191RL1Q225SBEA",
    #     start_date="2024-01-01",
    #     end_date="2026-01-01",
    #     frequency="daily",
    #     method="point-in-time"
    # )
    #
    # ml_data1 = client.get_ml_series(
    #     series_id="A191RL1Q225SBEA",
    #     start_date="2024-01-01",
    #     end_date="2026-01-01",
    #     frequency="daily",
    #     method="first"
    # )

    ml_data_diff = client.get_gdp_surprise_series(
        start_date="2024-01-01",
        end_date="2026-01-01",
    )

    # USEPUNEWSINDXM - Economic Uncertainty Index
    # EMVOVERALLEMV - Equity Market Volatility Index
    # STLENI - Real GDP Nowcast
    # BAMLH0A0HYM2 - HY Spread