import requests
from datetime import datetime, timezone, timedelta
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

    def get_daily_series(self, series_id: str, start_date: str) -> pd.DataFrame:
        """
        Returns a daily-indexed time series for a given series FRED ID.
        It gives the point-in-time data.
        """
        df = self.get_series(series_id, observation_start="1776-07-04",
                             return_full_history=True)

        # Standardize types and normalize dates
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['realtime_start'] = pd.to_datetime(df['realtime_start']).dt.normalize()
        df['realtime_end'] = pd.to_datetime(df['realtime_end']).dt.normalize()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # 2. Define the timeline (Start to UTC Today)
        end_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        timeline = pd.date_range(start=start_date, end=end_date, freq='D')

        daily_results = []

        # 3. Efficient Point-in-Time Scan
        # We iterate through the timeline to find the state of the world on that day
        for as_of in timeline:
            # What observations were "live" on this specific calendar date?
            mask = (df['realtime_start'] <= as_of) & (df['realtime_end'] >= as_of)
            valid_snapshot = df[mask]

            if not valid_snapshot.empty:
                # Of all valid observations, pick the one with the most recent observation_date
                # This handles the forward-filling naturally (e.g., seeing Dec data in Jan)
                latest_obs = valid_snapshot.sort_values('date', ascending=False).iloc[0]

                daily_results.append({
                    'date': as_of,
                    'value': latest_obs['value'],
                    'reference_period': latest_obs['date']
                })

            else:
                # Handle cases where no data was yet released for the start of the timeline
                daily_results.append({
                    'date': as_of,
                    'value': None,
                    'reference_period': None
                })

        result_df = pd.DataFrame(daily_results)

        # 4. Final Formatting
        result_df['date'] = result_df['date'].dt.strftime('%Y-%m-%d')
        result_df['reference_period'] = pd.to_datetime(result_df['reference_period']).dt.strftime('%Y-%m-%d')

        return result_df[['date', 'value', 'reference_period']]

    def get_release_events(self, series_id: str, start_date: str,
                           first_release_only=True) -> pd.DataFrame:

        # 1. Fetch FULL history - no start_date filter on the API call
        df = self.get_series(series_id, return_full_history=True)

        # 2. Standardize
        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['realtime_start'] = pd.to_datetime(df['realtime_start']).dt.normalize()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # 3. Compute revision numbers across full history first
        df = df.sort_values(['date', 'realtime_start'])
        df['revision_number'] = df.groupby('date').cumcount() + 1

        # 4. NOW filter to only rows where the release itself happened after start_date
        start_dt = pd.to_datetime(start_date).normalize()
        event_df = df[df['realtime_start'] >= start_dt].copy()

        # 5. Rename and format
        event_df = event_df.rename(columns={
            'realtime_start': 'release_date',
            'date': 'reference_period',
        })

        event_df['release_date'] = event_df['release_date'].dt.strftime('%Y-%m-%d')
        event_df['reference_period'] = event_df['reference_period'].dt.strftime('%Y-%m-%d')

        if first_release_only:
            event_df = event_df[event_df["revision_number"] == 1]

        return event_df[['release_date', 'reference_period', 'value',
                         'revision_number']].sort_values('release_date')

    def get_ml_series(self, series_id, start_date, end_date, frequency="daily", method="point-in-time"):
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
                    'revision_number': match['revision_number'],
                })
            else:
                ml_results.append({
                    'date': as_of,
                    'value': None,
                    'observation_date': None,
                    'revision_number': None,
                })

        result_df = pd.DataFrame(ml_results)

        # Final formatting: Ensure the 'date' column is just YYYY-MM-DD strings
        result_df['date'] = result_df['date'].dt.strftime('%Y-%m-%d')
        result_df['observation_date'] = result_df['observation_date'].dt.strftime('%Y-%m-%d')

        return result_df[['date', 'value', 'observation_date', 'revision_number']]

    def get_macro_surprise_panel(self, start_date, end_date, actual_ticker,
                                 forecast_config):
        """
        Args:
            start_date (str): 'YYYY-MM-DD'
            end_date (str): 'YYYY-MM-DD'
            actual_ticker (str): The FRED ticker for the actual data (e.g., "A191RL1Q225SBEA")
            forecast_config (dict): { "MODEL_NAME": "TICKER" }
                                     e.g., {"STLENI": "STLENI", "GDPNOW": "GDPNOW"}
        """
        start_dt = pd.to_datetime(start_date)
        buffered_start = (start_dt - timedelta(days=60)).strftime('%Y-%m-%d')

        # 1. Fetch the Actual series (buffered)
        actual_df = self.get_ml_series(actual_ticker, buffered_start, end_date,
                                       frequency="daily", method="first")
        actual_df = actual_df.rename(
            columns={'observation_date': 'ref_date_act',
                     'value': 'actual_val'})

        panel_results = []

        # 2. Iterate through N forecast series
        for model_name, ticker in forecast_config.items():
            forecast_df = self.get_ml_series(ticker, buffered_start, end_date,
                                             frequency="daily",
                                             method="point-in-time")

            forecast_df = forecast_df.rename(
                columns={'observation_date': 'ref_date_fcst',
                         'value': 'fcst_val'})

            # Merge Actual and current Forecast
            df = pd.merge(actual_df, forecast_df, on='date')
            df['date_dt'] = pd.to_datetime(df['date'])

            # Calculate Indicators
            df['is_release'] = df['ref_date_act'] != df['ref_date_act'].shift(1)
            df['prior_fcst'] = df['fcst_val'].shift(1)
            df['prior_ref_fcst'] = df['ref_date_fcst'].shift(1)

            for _, row in df.iterrows():
                if row['date_dt'] < start_dt:
                    continue

                # Default values for Forecast rows
                res_ref_date = row['ref_date_fcst']
                res_type = 'forecast'
                res_value = row['fcst_val']
                res_surprise = None

                # Pivot logic for Release Day
                if row['is_release']:
                    res_type = 'actual'
                    res_value = row['actual_val']
                    res_ref_date = row['ref_date_act']

                    if row['ref_date_act'] == row['prior_ref_fcst']:
                        res_surprise = row['actual_val'] - row['prior_fcst']
                    else:
                        res_surprise = 0.0

                # Calculate days_since_reference dynamically based on the active ref_date
                # This ensures that on release day, it measures against the ACTUAL quarter start
                days_since = (
                            row['date_dt'] - pd.to_datetime(res_ref_date)).days

                panel_results.append({
                    'date': row['date'],
                    'reference_date': res_ref_date,
                    'source': model_name,
                    'type': res_type,
                    'value': res_value,
                    'surprise': res_surprise,
                    'days_since_reference': days_since
                })

        # 3. Final DataFrame formatting
        df_final = pd.DataFrame(panel_results)
        df_final['date'] = pd.to_datetime(df_final['date']).dt.strftime(
            '%Y-%m-%d')
        df_final['reference_date'] = pd.to_datetime(
            df_final['reference_date']).dt.strftime('%Y-%m-%d')

        df_final = df_final.sort_values(['date', 'source'],
                                        ascending=[True, True])

        return df_final[
            ['date', 'reference_date', 'source', 'type', 'value', 'surprise',
             'days_since_reference']]


if __name__ == "__main__":
    api_key = "79bd13604bbe0db51d65ce6dfdca87fb"
    client = FredClient(api_key)

    # -------

    ml_data_daily = client.get_daily_series(
        series_id="CPIAUCSL",
        start_date="2025-01-01",
    )

    # -------

    ml_data_release = client.get_release_events(
        series_id="CPIAUCSL",
        start_date="2025-01-01",
    )

    # -------

    ml_data = client.get_ml_series(
        series_id="CPIAUCSL",
        start_date="2025-01-01",
        end_date="2026-01-01",
        frequency="daily",
        method="point-in-time"
    )

    # ------

    # Researchers define their models here
    my_forecasts = {
        "STLENI": "STLENI",
        "GDPNOW": "GDPNOW",
    }

    # One call returns the entire stacked panel
    df_panel = client.get_macro_surprise_panel(
        start_date="2024-01-01",
        end_date="2024-12-31",
        actual_ticker="A191RL1Q225SBEA",
        forecast_config=my_forecasts
    )

    # USEPUNEWSINDXM - Economic Uncertainty Index
    # EMVOVERALLEMV - Equity Market Volatility Index
    # STLENI - Real GDP Nowcast
    # BAMLH0A0HYM2 - HY Spread