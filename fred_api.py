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

        # Labels
        col_name = label if label else series_id

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
                    'reference_period': latest_obs['date'],
                    'series_id': col_name,
                    'value': latest_obs['value'],
                })

            else:
                # Handle cases where no data was yet released for the start of the timeline
                daily_results.append({
                    'date': as_of,
                    'reference_period': None,
                    'series_id': None,
                    'value': None,
                })

        df_result = pd.DataFrame(daily_results)

        # 4. Final Formatting
        df_result['date'] = df_result['date'].dt.strftime('%Y-%m-%d')
        df_result['reference_period'] = pd.to_datetime(df_result['reference_period']).dt.strftime('%Y-%m-%d')

        # ---

        df_result = df_result[['date', 'reference_period', 'series_id', 'value']]

        return df_result

    def get_release_events(self, series_id: str, start_date: str,
                           first_release_only: bool = True,
                           forecast_ids: list | None = None,
                           labels: dict | None = None) -> pd.DataFrame:
        """
        Returns a LONG format dataframe. Each row represents an actual release
        paired with a specific forecast source.
        """
        # 1. Fetch and Standardize Actuals
        df = self.get_series(series_id, return_full_history=True)
        labels = labels or {}

        df['date'] = pd.to_datetime(df['date']).dt.normalize()
        df['realtime_start'] = pd.to_datetime(
            df['realtime_start']).dt.normalize()
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # 2. Compute revision numbers
        df = df.sort_values(['date', 'realtime_start'])
        df['revision_number'] = df.groupby('date').cumcount() + 1

        # 3. Filter by start_date and format
        start_dt = pd.to_datetime(start_date).normalize()
        df_event = df[df['realtime_start'] >= start_dt].copy()

        if first_release_only:
            df_event = df_event[df_event["revision_number"] == 1]

        df_event = df_event.rename(columns={
            'realtime_start': 'release_date',
            'date': 'reference_period',
            'value': 'actual_value'  # Kept generic for the dictionary mapping
        })

        # Prepare IDs for the loop
        actual_label = labels.get(series_id, series_id)

        if not forecast_ids:
            # If no forecasts, return a simple table with the actual's label
            df_event['series_id'] = actual_label
            return df_event[['release_date', 'reference_period', 'series_id',
                             'actual_value', 'revision_number']]

        all_event_rows = []

        for f_id in forecast_ids:
            f_history = self.get_series(f_id, return_full_history=True)
            f_label = labels.get(f_id, f_id)

            # Standardize forecast history
            f_history['date'] = pd.to_datetime(
                f_history['date']).dt.normalize()
            f_history['realtime_start'] = pd.to_datetime(
                f_history['realtime_start']).dt.normalize()
            f_history['value'] = pd.to_numeric(f_history['value'],
                                               errors='coerce')

            for _, actual_row in df_event.iterrows():
                # Find the forecast released STRICTLY BEFORE the actual release
                f_match = f_history[
                    (f_history['date'] == actual_row['reference_period']) &
                    (f_history['realtime_start'] < actual_row['release_date'])
                    ]

                latest_f = \
                f_match.sort_values('realtime_start', ascending=False).iloc[0][
                    'value'] if not f_match.empty else None

                # Build the Long Row
                all_event_rows.append({
                    'release_date': actual_row['release_date'],
                    'reference_period': actual_row['reference_period'],
                    'series_id': actual_label,
                    'actual_value': actual_row['actual_value'],
                    'revision_number': actual_row['revision_number'],
                    'forecast_source': f_label,
                    'forecast_value': latest_f,
                    'surprise': actual_row[
                                    'actual_value'] - latest_f if latest_f is not None else None
                })

        # 4. Final DataFrame Construction
        result_df = pd.DataFrame(all_event_rows)

        # Sort by date then source for best scannability
        result_df = result_df.sort_values(
            by=['release_date', 'forecast_source'], ascending=[True, True])

        # Format dates to strings for final output
        result_df['release_date'] = result_df['release_date'].dt.strftime(
            '%Y-%m-%d')
        result_df['reference_period'] = result_df[
            'reference_period'].dt.strftime('%Y-%m-%d')

        return result_df

    def get_bulk_daily_series(self, series_ids: str | list[str],
                              start_date: str,
                              labels: dict | None = None) -> pd.DataFrame:

        if isinstance(series_ids, str):
            series_ids = [series_ids]

        labels = labels or {}
        all_dfs = []

        for s_id in series_ids:
            label = labels.get(s_id, s_id)
            df_single = self.get_daily_series(s_id, start_date, label=label)

            # In long format, we normalize the value column name
            # so they can all be stacked on top of each other
            val_col = f'value_{label}'
            if val_col in df_single.columns:
                df_single = df_single.rename(columns={val_col: 'value'})

            all_dfs.append(df_single)

        # Stack them all vertically
        df_long = pd.concat(all_dfs, axis=0)
        df_long = df_long.sort_values(['series_id', 'date'])

        return df_long


if __name__ == "__main__":
    api_key = "79bd13604bbe0db51d65ce6dfdca87fb"
    client = FredClient(api_key)

    # -------

    df_GDP = client.get_daily_series(
        series_id="A191RL1Q225SBEA",
        start_date="2025-01-01",
    )

    # -------

    df_gdp_surprise = client.get_release_events(
        series_id="A191RL1Q225SBEA",
        forecast_ids=['STLENI', 'GDPNOW'],
        start_date="2025-01-01",
        first_release_only=True,
        labels={"A191RL1Q225SBEA": "GDP",
                "STLENI": "STLENI",
                "GDPNOW": "GDPNOW"}
    )

    # -------

    # df_enriched = df_GDP.merge(
    #     df_gdp_surprise[['release_date', 'surprise_STLENI']],
    #     left_on='date',
    #     right_on='release_date',
    #     how='left'
    # )

    # -------

    df_long = client.get_bulk_daily_series(
        series_ids=["A191RL1Q225SBEA", "STLENI"],
        start_date="2025-01-01",
        labels={"A191RL1Q225SBEA": "GDP"}
    )

    # -------

    # USEPUNEWSINDXM - Economic Uncertainty Index
    # EMVOVERALLEMV - Equity Market Volatility Index
    # STLENI - Real GDP Nowcast
    # BAMLH0A0HYM2 - HY Spread