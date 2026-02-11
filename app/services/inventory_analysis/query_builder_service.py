from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection
from app.services.inventory_analysis.query_builder_utils import QueryBuilderUtils

class QueryBuilderService:
    def __init__(self):
        self.utils = QueryBuilderUtils()

    async def build_query(self, request: InventoryAnalysisRequestWithSelection, table_name: str) -> str:
        query = f"SELECT * FROM {table_name}"
        
        # Use dict keys to maintain insertion order like JS Set
        condition_set = {}
        order_set = {}

        if request.selections:
            selection_query, selection_conditions, selection_order_by = self.utils.build_selection_query(request, table_name=table_name)
            query = selection_query
            for c in selection_conditions:
                condition_set[c] = None
            
            if selection_order_by:
                parts = selection_order_by.replace("ORDER BY", "").split(",")
                for p in parts:
                    order_set[p.strip()] = None

        common_conditions = self.utils.build_common_filter_conditions(request)
        for c in common_conditions:
            condition_set[c] = None

        athena_conditions, athena_order_by = self.utils.build_athena_query_filters(request)
        for c in athena_conditions:
            condition_set[c] = None
        
        if athena_order_by:
            parts = athena_order_by.replace("ORDER BY", "").split(",")
            for p in parts:
                order_set[p.strip()] = None

        final_conditions = list(condition_set.keys())
        final_order = list(order_set.keys())

        if final_conditions:
            query += f" WHERE {' AND '.join(final_conditions)}"
        
        if final_order:
            query += f" ORDER BY {', '.join(final_order)}"

        return query

query_builder_service = QueryBuilderService()
