import pandas as pd
import numpy as np
from typing import Optional
from app.core.config import settings
from app.lib.s3_client import s3_client
from app.lib.logger import log
from app.lib.database import db_manager
from app.services.sales.sales_service import SalesService
from app.schemas.demand_forecast import DemandForecastParams, DemandForecastResponse
import json

from app.services.demand_forecast.base import IDemandForecastService
from app.core.client_config import ClientConfig

class TymDemandForecastService(IDemandForecastService):
    """
    TYM-specific implementation for handling Demand Forecast calculations.
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self.bucket = settings.AWS_S3_BUCKET
        self.forecast_parquet_file_key = config.s3_demand_forecast_parquet_key
        # Do not initialize sales_service here with a single session.
        # It should be initialized per request or use fresh sessions.
        self.forecast_uncertanity_filter_names = ["0.0062", "0.0228", "0.1587", "0.8413", "0.9772", "0.9938"]
        self.forecast_mean_filter_names = ["MeanPL"]
        self.prob_label_map = {
            0.9938: "99%",
            0.9772: "95%",
            0.8413: "68%",
            0.1587: "68%",
            0.0228: "95%",
            0.0062: "99%",
        }

    def get_forecast_explanation(self, params: DemandForecastParams) -> DemandForecastResponse:
        """
        Main entry point to fetch data and calculate metrics.
        """
        try:
            df = s3_client.read_parquet(bucket=self.bucket, key=self.forecast_parquet_file_key)

            return self._calculate_metrics(df, params)
        except Exception as e:
            log.exception(f"Failed to get demand forecast explanation: {e}")
            raise e

    def _calculate_metrics(self, df: pd.DataFrame, params: DemandForecastParams) -> DemandForecastResponse:
        """
        Internal method to coordinate calculations.
        """
        # Pre-process
        df['forecast_date'] = pd.to_datetime(df['forecast_date'])
        target_date = pd.to_datetime(params.forecast_date)
        
        # Filter Data
        filtered_df = self._filter_data(df, params, self.forecast_mean_filter_names)
        
        if filtered_df.empty:
            return DemandForecastResponse(
                forecasted_demand=0.0,
                average_demand_per_week=0.0,
                message=f"No data found for filters: {params.filter_name}={params.filter_value}"
            )

        # Calculate base forecasted demand
        result = self._calculate_forecasted_demand(filtered_df, target_date, params.period)
        
        if result is None:
            return DemandForecastResponse(
                forecasted_demand=0.0,
                average_demand_per_week=0.0,
                message=f"No data found for {target_date.strftime('%B %Y')}"
            )

        forecasted_demand, records_count = result

        # Calculate change vs previous month actual sales
        change_vs_last_month, prev_month_actual_sales, current_month_forecasted_demand = self._calculate_change_vs_previous_month_actual_sales(
                        filtered_df, 
                        target_date, 
                        params.company_id,
                        params.sales_type,
                        params.filter_value
                    )

        # Calculate change vs same month last year actual sales
        db = db_manager.get_session()
        try:
            sales_service = SalesService(db)
            change_vs_same_month_last_year, same_month_last_year_actual_sales, _ = self._calculate_change_vs_same_month_last_yeat(
                            sales_service=sales_service,
                            df=filtered_df, 
                            target_date=target_date, 
                            params=params
                        )
        finally:
            db.close()
        
        # Calculate coefficient of variation
        db = db_manager.get_session()
        try:
            sales_service = SalesService(db)
            coefficient_of_variation, actual_sales_yoy_percentage_changes = self._calculate_cv(
                            sales_service=sales_service,
                            company_id=params.company_id,
                            sales_type=params.sales_type,
                            region_name=params.filter_value,
                            target_date=target_date
                        )
        finally:
            db.close()
        
        # Calculate confidence and uncertainty if the request period is monthly
        filtered_df = self._filter_data(df, params, self.forecast_uncertanity_filter_names)
        
        confidence_interval = None
        if params.period == "monthly":
            confidence_interval = self._get_forecast_confidence(
                            df=filtered_df,
                            target_date=target_date
                        )

        # Calculate Seasonality and Trend for if the requested filter_name is specific Region and not all Region
        seasonality = None
        trend = None

        if params.filter_name == "Region" and params.filter_value.lower() != "all":
            try:
                # Use a dict-returning method for configuration JSONs
                region_time_series_config = s3_client.read_json_as_dict(bucket=self.bucket, key=self.config.s3_region_time_series_config_key)

                if params.filter_value in region_time_series_config:
                    seasonality, trend = self._calculate_seasonality_and_trend(
                        target_date=target_date,
                        region_time_series_config=region_time_series_config,
                        region_name=params.filter_value
                    )
                else:
                    log.warning(f"Region {params.filter_value} not found in time series config")
            except Exception as e:
                log.error(f"Error calculating seasonality and trend: {e}")
        

        # Assemble final response
        return DemandForecastResponse(
            forecasted_demand=round(float(forecasted_demand), 2),
            average_demand_per_week=self._calculate_average_per_week(forecasted_demand, records_count),
            change_vs_last_month_actual_sales=change_vs_last_month,
            prev_month_actual_sales=prev_month_actual_sales,
            current_month_forecasted_demand=current_month_forecasted_demand,
            change_vs_same_month_last_year=change_vs_same_month_last_year,
            same_month_last_year_actual_sales=same_month_last_year_actual_sales,
            coefficient_of_variation=coefficient_of_variation,
            actual_sales_yoy_percentage_changes=actual_sales_yoy_percentage_changes,
            seasonality=seasonality,
            trend=trend,
            confidence_interval=confidence_interval,
            metadata={
                "target_date": str(target_date.date()),
                "filter_name": params.filter_name,
                "filter_value": params.filter_value,
                "series_id": params.series_id,
                "period": params.period,
            }
        )

    def _filter_data(self, df: pd.DataFrame, params: DemandForecastParams, forecast_filter_names: list[str] = ["MeanPL", "MedianPL", "ModePL"]) -> pd.DataFrame:
        """
        Filters the dataframe based on Name, Filter Name, Filter Value and Series ID.
        """
        mask = (df['name'].isin(forecast_filter_names)) & \
               (df['filter_name'] == params.filter_name) & \
               (df['filter_value'] == params.filter_value) & \
               (df['series_id'] == params.series_id)

        return df[mask].copy()

    def _calculate_forecasted_demand(self, df: pd.DataFrame, target_date: pd.Timestamp, period: str) -> Optional[tuple[float, int]]:
        """
        Calculates forecasted demand based on cumulative or monthly logic.
        """
        # Identify current month data
        current_month_mask = (df['forecast_date'].dt.year == target_date.year) & \
                             (df['forecast_date'].dt.month == target_date.month)
        current_month_data = df[current_month_mask]
        
        if current_month_data.empty:
            return None
        
        # Last available date of the target month
        last_date_current = current_month_data['forecast_date'].max()
        current_cum = float(current_month_data[current_month_data['forecast_date'] == last_date_current]['prediction_cum'].iloc[0])

        if period.lower() == "monthly":
            
            return self._get_current_month_forecasted_demand(df, target_date)

        # Default/Cumulative
        prev_all_data = df[df['forecast_date'].dt.to_period('M') <= target_date.to_period('M')]
        
        return current_cum, prev_all_data.shape[0]

    def _calculate_average_per_week(self, forecasted_demand: float, records_count: int) -> float:
        """
        Calculates average demand per week.
        """
        return round(float(forecasted_demand / records_count), 2)

    def _calculate_change_vs_previous_month_actual_sales(self, df: pd.DataFrame, target_date: pd.Timestamp, company_id: str, sales_type: str, region_name: str) -> tuple[float, float, float]:
        """
        Calculates the percentage change for current month forecasted demand vs previous month's actual sales.
        Uses the Sales table for actual sales data.
        """
        try:
            # Get forecasted demand for the current target month
            forecast_result = self._get_current_month_forecasted_demand(df, target_date)
            if not forecast_result:
                return 0.0, 0.0, 0.0
            
            current_month_forecasted_demand, _ = forecast_result

            # Calculate previous month for actual sales comparison
            # e.g. if target_date is 2026-02-07, previous month is 2026-01
            first_day_current = target_date.replace(day=1)
            prev_month_date = first_day_current - pd.DateOffset(months=1)
            
            prev_month = prev_month_date.month
            prev_year = prev_month_date.year

            # Fetch actual sales from DB
            db = db_manager.get_session()
            try:
                sales_service = SalesService(db)
                prev_month_actual_sales = sales_service.get_monthly_sales_total(
                    company_id=company_id,
                    year=prev_year,
                    month=prev_month,
                    sales_type=sales_type,
                    region_name=region_name
                )
            finally:
                db.close()

            if prev_month_actual_sales == 0 or prev_month_actual_sales is None:
                log.warning(f"No actual sales data found for {prev_year}-{prev_month}")
                return 0.0, float(prev_month_actual_sales or 0), current_month_forecasted_demand

            change = ((current_month_forecasted_demand - prev_month_actual_sales) / prev_month_actual_sales) * 100
            return round(change, 2), float(prev_month_actual_sales), current_month_forecasted_demand
            
        except Exception as e:
            log.exception(f"Error calculating change vs previous month actual sales: {e}")
            return 0.0, 0.0, 0.0

    def _calculate_change_vs_same_month_last_yeat(self, sales_service: SalesService, df: pd.DataFrame, target_date: pd.Timestamp, params: DemandForecastParams) -> tuple[float, float, float]:
        """
        Calculates the percentage change for current month forecasted demand vs same month last year.
        Uses the Sales table for actual sales data.
        """
        try:
            # Get forecasted demand for the current target month
            forecast_result = self._get_current_month_forecasted_demand(df, target_date)
            if not forecast_result:
                return 0.0, 0.0, 0.0
            
            current_month_forecasted_demand, _ = forecast_result

            # Calculate same month last year for actual sales comparison
            same_month_last_year = target_date.replace(year=target_date.year - 1)
            
            try:
                same_month_last_year_actual_sales = sales_service.get_monthly_sales_total(
                    company_id=params.company_id,
                    year=same_month_last_year.year,
                    month=same_month_last_year.month,
                    sales_type=params.sales_type,
                    region_name=params.filter_value
                )
            except Exception as e:
                log.exception(f"Error calculating change vs same month last year actual sales: {e}")
                return 0.0, 0.0, 0.0

            
            if same_month_last_year_actual_sales == 0 or same_month_last_year_actual_sales is None:
                log.warning(f"No actual sales data found for {same_month_last_year.year}-{same_month_last_year.month}")
                return 0.0, float(same_month_last_year_actual_sales or 0), current_month_forecasted_demand

            change = ((current_month_forecasted_demand - same_month_last_year_actual_sales) / same_month_last_year_actual_sales) * 100
            return round(change, 2), float(same_month_last_year_actual_sales), current_month_forecasted_demand
            
        except Exception as e:
            log.exception(f"Error calculating change vs same month last year actual sales: {e}")
            return 0.0, 0.0, 0.0
    
    def _calculate_cv(self, sales_service: SalesService, target_date: pd.Timestamp, company_id: str, sales_type: str, region_name: str) -> tuple[float, list[float]]:
        try:
            forecast_result = sales_service.get_last_12_months_yoy_sales_total(
                company_id=company_id,
                sales_type=sales_type,
                region_name=region_name
            )
            
            if not forecast_result or len(forecast_result) == 0:
                log.warning("No sales data found for CV calculation")
                return 0.0
            
            # Organize data by month
            months_data = {}
            for row in forecast_result:
                month = row['SalesMonth']
                if month not in months_data:
                    months_data[month] = []
                months_data[month].append(row)

            percentage_changes = []
            for month, data in months_data.items():
                if len(data) >= 2:
                    # Sort by year to ensure we compare two consecutive or available years
                    sorted_data = sorted(data, key=lambda x: x['SalesYear'])
                    # Take the two most recent available years for this month
                    curr_year_sales = sorted_data[-1]['TotalUnitsSold']
                    prev_year_sales = sorted_data[-2]['TotalUnitsSold']
                    
                    if prev_year_sales > 0:
                        change = (curr_year_sales - prev_year_sales) / prev_year_sales
                        percentage_changes.append(change)
            
            if not percentage_changes:
                log.warning("Not enough year-over-year data points for CV calculation")
                return 0.0
            
            # Calculate mean and standard deviation
            mean_change = np.mean(percentage_changes)
            std_change = np.std(percentage_changes)
            
            if mean_change == 0:
                return 0.0
                
            cv = std_change / mean_change
            log.info(f"CV Calculation Points: {percentage_changes}")
            log.info(f"CV Calculation Stats: mean={mean_change:.4f}, std={std_change:.4f}, cv={cv:.4f}")
            
            return round(float(cv), 4), percentage_changes

        except Exception as e:
            log.exception(f"Error calculating CV: {e}")
            return 0.0

    def _get_forecast_confidence(self, df: pd.DataFrame, target_date: pd.Timestamp) -> Optional[dict]:
        
        """ 
            Returns the forecasted confidence for the current month.
        """

        # Get the current month last date data
        current_month_mask = (df['forecast_date'].dt.year == target_date.year) & \
                             (df['forecast_date'].dt.month == target_date.month)
        
        current_month_data = df[current_month_mask]

        if current_month_data.empty:
            return None

        last_date_current = current_month_data['forecast_date'].max()

        last_date_current_data = current_month_data[current_month_data['forecast_date'] == last_date_current]

        last_date_current_data = last_date_current_data.copy()
        last_date_current_data["label"] = last_date_current_data["name"].astype(float).round(4).map(self.prob_label_map)

        result = {
            "upper_bound": (
                last_date_current_data[last_date_current_data["sigma"].astype(float) > 0]
                .set_index("label")["prediction_cum"]
                .to_dict()
            ),
            "lower_bound": (
                last_date_current_data[last_date_current_data["sigma"].astype(float) < 0]
                .set_index("label")["prediction_cum"]
                .to_dict()
            )
        }

        return result

    
    def _calculate_seasonality_and_trend(self, target_date: pd.Timestamp, region_time_series_config: dict, region_name: str) -> tuple[float, float]:
        """ 
        Returns the seasonality and trend for the given region.
        """
        try:
            region_config = region_time_series_config[region_name]
            
            # Use isocalendar week but be careful with year boundaries
            start_week = target_date.replace(day=1).isocalendar().week
            end_week = (target_date.replace(day=1) + pd.offsets.MonthEnd(1)).isocalendar().week
            
            # Seasonality list (usually 1-indexed by week number 1-52/53)
            week_of_year_seasonality = region_config.get('week_of_year_seasonality', [])
            if not week_of_year_seasonality:
                return 0.0, 0.0

            # Handle end < start (Dec/Jan boundary)
            if end_week < start_week:
                # Approximate for boundary cases or handle properly
                # For now, let's just take 4 weeks if it's a wrap-around
                indices = list(range(start_week - 1, len(week_of_year_seasonality))) + \
                          list(range(0, end_week))
            else:
                indices = list(range(start_week - 1, end_week))

            # Limit to max 5 weeks as per user requirements
            if len(indices) > 5:
                indices = indices[:5]

            # Safe sum with bounds checking
            seasonality = sum(week_of_year_seasonality[i] for i in indices if 0 <= i < len(week_of_year_seasonality))
            
            # Trend
            trend_values = region_config.get('trend_values', [])
            trend = trend_values[-1] if trend_values else 0.0

            return float(seasonality), float(trend)
            
        except Exception as e:
            log.error(f"Error in _calculate_seasonality_and_trend: {e}")
            return 0.0, 0.0


    def _get_current_month_forecasted_demand(self, df: pd.DataFrame, target_date: pd.Timestamp) -> Optional[tuple[float, int]]:
        
        """ 
            Returns the forecasted demand for the current month.
        """

        # Identify current month data
        current_month_mask = (df['forecast_date'].dt.year == target_date.year) & \
                             (df['forecast_date'].dt.month == target_date.month)
        current_month_data = df[current_month_mask]
        
        if current_month_data.empty:
            return None

        # Last available date of the target month
        last_date_current = current_month_data['forecast_date'].max()
        current_cum = float(current_month_data[current_month_data['forecast_date'] == last_date_current]['prediction_cum'].iloc[0])

        first_day_of_month = target_date.replace(day=1)
        prev_data = df[df['forecast_date'] < first_day_of_month]
            
        if not prev_data.empty:
            last_date_prev = prev_data['forecast_date'].max()
            prev_cum = float(prev_data[prev_data['forecast_date'] == last_date_prev]['prediction_cum'].iloc[0])
            monthly_demand = current_cum - prev_cum

            # Calculate the number of records between last_date_prev and last_date_current
            data_count = df[(df['forecast_date'] <= last_date_current) & (df['forecast_date'] > last_date_prev)]

            return monthly_demand, data_count.shape[0]

        # If no previous month data is available, return the current month's cumulative demand        
        return current_cum, len(current_month_data)
