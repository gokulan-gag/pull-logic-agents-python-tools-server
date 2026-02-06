from dateutil.relativedelta import relativedelta
from datetime import date
from app.repos.sales.sales_repo import SalesRepo
from sqlalchemy.orm import Session

class SalesService:
    def __init__(self, db: Session):
        self.repo = SalesRepo(db)

    def get_monthly_sales_total(
        self, 
        company_id: str, 
        year: int, 
        month: int,
        sales_type: str,
        region_name: str
    ) -> float:
        """
        Calculates the total units sold for a specific company in a given month.
        """
        start_date = date(year, month, 1)
        # Handle year rollover for next month
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        total_units_sold = self.repo.get_units_sold_by_company_and_date_range(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            sales_type=sales_type,
            region_name=region_name
        )

        return total_units_sold

    def get_last_12_months_yoy_sales_total(
        self, 
        company_id: str, 
        sales_type: str,
        region_name: str
    ) -> float:
        """
        Calculates the total units sold for a specific company in a given month.
        """
        # From today to 24 months ago, because the sales data is available from the last month
        today = date.today()
        end_date = today.replace(day=1)
        start_date = end_date - relativedelta(months=24)

        result = self.repo.get_yoy_sales_total(
            company_id=company_id,
            start_date=start_date,
            end_date=end_date,
            sales_type=sales_type,
            region_name=region_name
        )

        return result