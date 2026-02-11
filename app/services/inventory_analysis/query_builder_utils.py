import re
from typing import List, Optional, Any, Tuple
from app.core.config import settings
from app.schemas.inventory_analysis import (
    InventoryAnalysisRequest, 
    InventoryAnalysisRequestWithSelection,
    ConditionalValues,
    Condition,
    SelectionOperations
)

class QueryBuilderUtils:
    @staticmethod
    def format_field(field: str) -> str:
        is_expression = bool(re.search(r'[\+\-\*\/\%\(\)]', field))
        return field if is_expression else f'"{field}"'

    @staticmethod
    def parse_if_number(value: Any) -> Any:
        if isinstance(value, str):
            try:
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return f"\"{value}\""
        if isinstance(value, (int, float)):
            return value
        return f"\"{value}\""

    @staticmethod
    def condition_to_sql(field: str, v: ConditionalValues) -> Optional[str]:
        if not v.condition:
            return None
        
        f = QueryBuilderUtils.format_field(field)
        
        if v.condition == Condition.EQUALS_TO and v.equals is not None:
            return f"CAST({f} AS DOUBLE) = {QueryBuilderUtils.parse_if_number(v.equals)}"
        
        if v.condition == Condition.NOT_EQUALS_TO and v.equals is not None:
            return f"CAST({f} AS DOUBLE) != {QueryBuilderUtils.parse_if_number(v.equals)}"
        
        if v.condition == Condition.GREATER_THAN and v.min is not None:
            return f"CAST({f} AS DOUBLE) > {QueryBuilderUtils.parse_if_number(v.min)}"
        
        if v.condition == Condition.LESSER_THAN and v.max is not None:
            return f"CAST({f} AS DOUBLE) < {QueryBuilderUtils.parse_if_number(v.max)}"
        
        if v.condition == Condition.GREATER_THAN_EQUALS and v.min is not None:
            return f"CAST({f} AS DOUBLE) >= {QueryBuilderUtils.parse_if_number(v.min)}"
        
        if v.condition == Condition.LESSER_THAN_EQUALS and v.max is not None:
            return f"CAST({f} AS DOUBLE) <= {QueryBuilderUtils.parse_if_number(v.max)}"
        
        if v.condition == Condition.GREATER_AND_LESSER_EQUALS and v.min is not None and v.max is not None:
            return f"CAST({f} AS DOUBLE) >= {QueryBuilderUtils.parse_if_number(v.min)} AND CAST({f} AS DOUBLE) <= {QueryBuilderUtils.parse_if_number(v.max)}"
        
        if v.condition == Condition.GREATER_AND_LESSER and v.min is not None and v.max is not None:
            return f"CAST({f} AS DOUBLE) > {QueryBuilderUtils.parse_if_number(v.min)} AND CAST({f} AS DOUBLE) < {QueryBuilderUtils.parse_if_number(v.max)}"
        
        return None

    @staticmethod
    def build_common_filter_conditions(request: InventoryAnalysisRequest) -> List[str]:
        conditions = []
        if request.sku: conditions.append(f"sku = '{request.sku}'")
        if request.supplier: conditions.append(f"supplier = '{request.supplier}'")
        if request.main_category: conditions.append(f"\"main category\" = '{request.main_category}'")
        if request.sub_category: conditions.append(f"\"sub category\" = '{request.sub_category}'")
        if request.sub_category2: conditions.append(f"\"sub category2\" = '{request.sub_category2}'")
        if request.lifecycle: conditions.append(f"lifecycle = '{request.lifecycle}'")
        if request.abc_code: conditions.append(f"\"abc code\" = '{request.abc_code}'")

        if request.target_service_level and request.target_service_level.condition:
            v = request.target_service_level
            numeric = v.equals if v.equals is not None else (v.max if v.max is not None else v.min)
            if numeric is not None:
                conditions.append(f"\"target service level\" = {numeric}")
        
        return conditions

    @staticmethod
    def build_athena_query_filters(filters: InventoryAnalysisRequest) -> Tuple[List[str], str]:
        conditions = []
        order_parts = []
        
        # We need to iterate over numeric fields
        numeric_fields = [
            "moq", "expected lead time (days)", "transit days", "buffer days",
            "on-hand inventory", "available", "on orders to vendors",
            "in-transit inventory", "total inventory", "current robust autonomy",
            "target autonomy", "target inventory", "replenishment quantity",
            "replenishment quantity (without moq)", "expected lost sales"
        ]
        
        filter_dict = filters.model_dump(by_alias=True, exclude_none=True)
        
        for field in numeric_fields:
            if field in filter_dict and isinstance(filter_dict[field], dict):
                v_dict = filter_dict[field]
                v = ConditionalValues(**v_dict)
                if v.condition:
                    sql = QueryBuilderUtils.condition_to_sql(field, v)
                    if sql:
                        conditions.append(sql)
                
                if v.sortBy:
                    order_parts.append(f"\"{field}\" {v.sortBy.value}")
        
        order_by = f"ORDER BY {', '.join(order_parts)}" if order_parts else ""
        return conditions, order_by

    @staticmethod
    def build_selection_query(request: InventoryAnalysisRequestWithSelection, table_name: str) -> Tuple[str, List[str], str]:
        selection_fields = request.selections or []
        unique_selections = []
        order_parts = []
        conditions = []

        op_map = {
            "add": "+",
            "diff": "-",
            "multiply": "*",
            "division": "/",
            "modulo": "%"
        }

        for field in selection_fields:
            if isinstance(field, str):
                if field == "*":
                    unique_selections.append("*")
                else:
                    unique_selections.append(f"\"{field}\"")
            elif isinstance(field, SelectionOperations) or isinstance(field, dict):
                if isinstance(field, dict):
                    field = SelectionOperations(**field)
                
                op = op_map.get(field.operation.value)
                if not op:
                    raise Exception(f"Unknown operation: {field.operation}")
                
                val_a = QueryBuilderUtils.parse_if_number(field.value_a)
                val_b = QueryBuilderUtils.parse_if_number(field.value_b)
                
                raw_expr = f"({val_a} {op} {val_b})"
                expr_with_alias = f"{raw_expr} AS \"{field.alias}\""
                
                unique_selections.append(expr_with_alias)
                
                if field.sortBy:
                    order_parts.append(f"\"{field.alias}\" {field.sortBy.value}")
                
                if field.comparison and field.comparison.condition:
                    sql = QueryBuilderUtils.condition_to_sql(raw_expr, field.comparison)
                    if sql:
                        conditions.append(sql)
        
        selections_str = ", ".join(unique_selections)
        order_by = f"ORDER BY {', '.join(order_parts)}" if order_parts else ""
        
        query = f"SELECT *, {selections_str} FROM {table_name}" if selections_str else f"SELECT * FROM {table_name}"
        
        return query, conditions, order_by
