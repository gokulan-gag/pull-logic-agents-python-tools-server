from enum import Enum
from typing import List, Optional, Union, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class SortBy(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

class Condition(str, Enum):
    EQUALS_TO = "equals_to"
    NOT_EQUALS_TO = "not_equals_to"
    GREATER_THAN = "greater_than"
    LESSER_THAN = "lesser_than"
    GREATER_THAN_EQUALS = "greater_than_equals"
    LESSER_THAN_EQUALS = "lesser_than_equals"
    GREATER_AND_LESSER_EQUALS = "greater_and_lesser_equals"
    GREATER_AND_LESSER = "greater_and_lesser"

class Operations(str, Enum):
    ADD = "add"
    DIFF = "diff"
    MULTIPLY = "multiply"
    DIVISION = "division"
    MODULO = "modulo"

class ConditionalValues(BaseModel):
    condition: Optional[Condition] = None
    min: Optional[Union[float, int, str]] = None
    max: Optional[Union[float, int, str]] = None
    equals: Optional[Union[float, int, str]] = None
    sortBy: Optional[SortBy] = None
    orderBy: Optional[bool] = None

class SelectionOperations(BaseModel):
    operation: Operations
    value_a: Union[str, float, int]
    value_b: Union[str, float, int]
    alias: str
    sortBy: Optional[SortBy] = None
    comparison: Optional[ConditionalValues] = None

class PaginatedResult(BaseModel, Generic[T]):
    executionId: str
    nextToken: Optional[str] = None
    hasMore: bool
    results: List[T]

class Inventory(BaseModel):
    supplier: Optional[str] = None
    port_of_departure: Optional[str] = Field(None, alias="port of departure")
    category: Optional[str] = None
    sku: Optional[str] = None
    type: Optional[str] = None
    lifecycle: Optional[str] = None
    moq: Optional[str] = None
    expected_lead_time_days: Optional[str] = Field(None, alias="expected lead time (days)")
    transit_days: Optional[str] = Field(None, alias="transit days")
    on_hand_inventory: Optional[str] = Field(None, alias="on-hand inventory")
    available: Optional[str] = None
    on_orders_to_vendors: Optional[str] = Field(None, alias="on orders to vendors")
    in_transit_inventory: Optional[str] = Field(None, alias="in-transit inventory")
    total_inventory: Optional[str] = Field(None, alias="total inventory")
    customer_open_orders: Optional[str] = Field(None, alias="customer open orders")
    customer_allocated_orders: Optional[str] = Field(None, alias="customer allocated orders")
    customer_back_orders: Optional[str] = Field(None, alias="customer back orders")
    customer_future_orders: Optional[str] = Field(None, alias="customer future orders")
    oldgen_pipe_total: Optional[str] = Field(None, alias="oldgen pipe total")
    current_robust_autonomy: Optional[str] = Field(None, alias="current robust autonomy")
    target_autonomy: Optional[str] = Field(None, alias="target autonomy")
    target_service_level: Optional[str] = Field(None, alias="target service level")
    target_inventory: Optional[str] = Field(None, alias="target inventory")
    quantity: Optional[str] = None
    replenishment_quantity: Optional[str] = Field(None, alias="replenishment quantity")
    replenishment_quantity_without_moq: Optional[str] = Field(None, alias="replenishment quantity (without moq)")
    
    class Config:
        populate_by_name = True

class InventoryAnalysisRequest(BaseModel):
    limit: Optional[int] = 20
    executionId: Optional[str] = None
    nextToken: Optional[str] = None
    sku: Optional[str] = None
    supplier: Optional[str] = None
    main_category: Optional[str] = Field(None, alias="main Category")
    sub_category: Optional[str] = Field(None, alias="sub Category")
    sub_category2: Optional[str] = Field(None, alias="sub Category2")
    lifecycle: Optional[str] = None
    abc_code: Optional[str] = Field(None, alias="abc code")
    target_service_level: Optional[ConditionalValues] = Field(None, alias="target service level")
    
    # Numeric filters
    moq: Optional[ConditionalValues] = None
    expected_lead_time_days: Optional[ConditionalValues] = Field(None, alias="expected lead time (days)")
    transit_days: Optional[ConditionalValues] = Field(None, alias="transit days")
    buffer_days: Optional[ConditionalValues] = Field(None, alias="buffer days")
    on_hand_inventory: Optional[ConditionalValues] = Field(None, alias="on-hand inventory")
    available: Optional[ConditionalValues] = None
    on_orders_to_vendors: Optional[ConditionalValues] = Field(None, alias="on orders to vendors")
    in_transit_inventory: Optional[ConditionalValues] = Field(None, alias="in-transit inventory")
    total_inventory: Optional[ConditionalValues] = Field(None, alias="total inventory")
    current_robust_autonomy: Optional[ConditionalValues] = Field(None, alias="current robust autonomy")
    target_autonomy: Optional[ConditionalValues] = Field(None, alias="target autonomy")
    target_inventory: Optional[ConditionalValues] = Field(None, alias="target inventory")
    replenishment_quantity: Optional[ConditionalValues] = Field(None, alias="replenishment quantity")
    replenishment_quantity_without_moq: Optional[ConditionalValues] = Field(None, alias="replenishment quantity (without moq)")
    expected_lost_sales: Optional[ConditionalValues] = Field(None, alias="expected lost sales")

    class Config:
        populate_by_name = True

class InventoryAnalysisRequestWithSelection(InventoryAnalysisRequest):
    selections: Optional[List[Union[str, SelectionOperations]]] = None

class InventoryAnalysisOutput(BaseModel):
    results: str
    executionId: str
    nextToken: Optional[str] = None
    hasMore: bool
    count: int
