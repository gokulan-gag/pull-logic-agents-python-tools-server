from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from sqlalchemy.dialects import mssql


class SalesRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_units_sold_by_company_and_date_range(
        self, 
        company_id: str, 
        start_date: date, 
        end_date: date,
        sales_type: str,
        region_name: str
    ) -> float:
        """
        Fetches UnitsSold and SalesDate from the Sales table for a specific company and date range.
        """
        query_str = """
            SELECT 
                SUM(s.UnitsSold) AS TotalUnitsSold 
            FROM Sales s
            LEFT JOIN Dealer d ON d.DealerID = s.DealerID
            LEFT JOIN CorporateRegion cr ON cr.RegionID = d.CorporateRegionID
            WHERE s.CompanyID = :company_id
                AND s.SalesType = :sales_type
                AND SalesDate >= :start_date
                AND SalesDate <  :end_date
        """
        
        params = {
            "company_id": company_id,
            "sales_type": sales_type,
            "start_date": start_date,
            "end_date": end_date
        }

        if region_name and region_name.lower() != "all":
            query_str += " AND cr.RegionName = :region_name"
            params["region_name"] = region_name

        stmt = text(query_str).bindparams(**params)

        compiled = stmt.compile(
            dialect=mssql.dialect(),
            compile_kwargs={"literal_binds": True}
        )

        # print("Executing SQL:")
        # print(compiled)

        result = self.db.execute(text(query_str), params)

        return result.scalar_one_or_none()

    def get_yoy_sales_total(
        self, 
        company_id: str, 
        start_date: date, 
        end_date: date,
        sales_type: str,
        region_name: str
    ) -> float:
        """
        Fetches UnitsSold and SalesDate from the Sales table for a specific company and date range.
        """
        query_str = """
            SELECT 
                YEAR(SalesDate) AS SalesYear,
                MONTH(SalesDate) AS SalesMonth,
                SUM(s.UnitsSold) AS TotalUnitsSold
            FROM Sales s
            LEFT JOIN Dealer d ON d.DealerID = s.DealerID
            LEFT JOIN CorporateRegion cr ON cr.RegionID = d.CorporateRegionID
            WHERE s.CompanyID = :company_id
            AND s.SalesType = :sales_type
            AND SalesDate >= :start_date
            AND SalesDate <  :end_date
        """
        
        params = {
            "company_id": company_id,
            "sales_type": sales_type,
            "start_date": start_date,
            "end_date": end_date
        }

        if region_name and region_name.lower() != "all":
            query_str += " AND cr.RegionName = :region_name"
            params["region_name"] = region_name

        query_str += """
            GROUP BY 
                YEAR(SalesDate),
                MONTH(SalesDate)
            ORDER BY SalesMonth;
        """

        stmt = text(query_str).bindparams(**params)

        compiled = stmt.compile(
            dialect=mssql.dialect(),
            compile_kwargs={"literal_binds": True}
        )

        # print("Executing SQL:")
        # print(compiled)

        result = self.db.execute(text(query_str), params)

        from app.lib.logger import log
        log.info(f"Result fetched: {result}")
        
        return [dict(row._mapping) for row in result]