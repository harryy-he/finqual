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

    def get_daily_series(self, series_id: str, start_date: str, label: str|None = None) -> pd.DataFrame:
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

        # ---

        col_name = label if label else series_id
        result_df = result_df.rename(columns={'value': f'value_{col_name}'})

        result_df = result_df[['date', f'value_{col_name}', 'reference_period']]

        return result_df

    def get_release_events(self, series_id: str, start_date: str,
                           first_release_only: bool = True,
                           forecast_ids: list|None = None,
                           label: str|None = None) -> pd.DataFrame:

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
        df_event = df[df['realtime_start'] >= start_dt].copy()

        # 5. Rename and format
        df_event = df_event.rename(columns={
            'realtime_start': 'release_date',
            'date': 'reference_period',
        })

        df_event['release_date'] = df_event['release_date'].dt.strftime('%Y-%m-%d')
        df_event['reference_period'] = df_event['reference_period'].dt.strftime('%Y-%m-%d')

        if first_release_only:
            df_event = df_event[df_event["revision_number"] == 1]

        df_event = df_event[['release_date', 'reference_period', 'value', 'revision_number']]
        df_event = df_event.sort_values(by=['release_date', 'reference_period'], ascending=[True, True])

        if not forecast_ids:

            col_name = label if label else series_id
            df_event = df_event.rename(columns={'value': f'value_{col_name}'})

            return df_event

        for f_id in forecast_ids:
            # 1. Get the forecast's own release/revision history
            # We need the full history to match specific reference periods
            f_history = self.get_series(f_id, return_full_history=True)

            # Standardize forecast history
            f_history['date'] = pd.to_datetime(f_history['date']).dt.normalize()
            f_history['realtime_start'] = pd.to_datetime(f_history['realtime_start']).dt.normalize()
            f_history['value'] = pd.to_numeric(f_history['value'], errors='coerce')

            # 2. Prepare to store the "matched" forecast for each actual release
            matched_forecasts = []

            for idx, actual_row in df_event.iterrows():
                ref_p = pd.to_datetime(actual_row['reference_period'])
                rel_d = pd.to_datetime(actual_row['release_date'])

                # Filter forecast history for:
                # - The SAME reference period as the actual
                # - Released ON or BEFORE the actual's release_date
                f_match = f_history[
                    (f_history['date'] == ref_p) &
                    (f_history['realtime_start'] <= rel_d)
                    ]

                if not f_match.empty:
                    # Take the absolute latest forecast for that specific period
                    latest_f = f_match.sort_values('realtime_start', ascending=False).iloc[0]['value']
                else:
                    latest_f = None

                matched_forecasts.append(latest_f)

            # 3. Add the columns to the dataframe
            df_event[f'forecast_{f_id}'] = matched_forecasts
            df_event[f'surprise_{f_id}'] = df_event['value'] - df_event[f'forecast_{f_id}']

        df_event = df_event.sort_values(by=['release_date', 'reference_period'], ascending=[True, True])

        col_name = label if label else series_id
        df_event = df_event.rename(columns={'value': f'value_{col_name}'})

        return df_event

if __name__ == "__main__":
    api_key = "79bd13604bbe0db51d65ce6dfdca87fb"
    client = FredClient(api_key)

    # -------

    STLENI_data_daily = client.get_daily_series(
        series_id="STLENI",
        start_date="2025-01-01",
    )

    GDPNOW_data_daily = client.get_daily_series(
        series_id="GDPNOW",
        start_date="2025-01-01",
    )

    # -------

    ml_data_release = client.get_release_events(
        series_id="A191RL1Q225SBEA",
        forecast_ids=['STLENI', 'GDPNOW'],
        start_date="2025-01-01",
        label="real_gdp_growth"
    )

    # -------

    # USEPUNEWSINDXM - Economic Uncertainty Index
    # EMVOVERALLEMV - Equity Market Volatility Index
    # STLENI - Real GDP Nowcast
    # BAMLH0A0HYM2 - HY Spread