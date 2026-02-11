from typing import Dict, Any, Optional
from pydantic import BaseModel

class ClientConfig(BaseModel):
    name: str
    s3_demand_forecast_parquet_key: Optional[str] = None
    s3_region_time_series_config_key: Optional[str] = None
    s3_athena_output_location: Optional[str] = None
    athena_database: Optional[str] = None
    athena_workgroup: Optional[str] = None
    inventory_replenishment_table: Optional[str] = None

# Configuration Store
# Mapping from Company ID to ClientConfig
CLIENT_CONFIGS: Dict[str, ClientConfig] = {
    # TYM Client
    "f80d6409-cb1d-4af1-8e1c-1b90f657b9bd": ClientConfig(
        name="TYM",
        s3_demand_forecast_parquet_key="computationfiles/f80d6409-cb1d-4af1-8e1c-1b90f657b9bd/963b770e-595f-4f76-a172-503246d6cf13/data-analytics/demand-forecast/demand_forecast.parquet",
        s3_region_time_series_config_key="computationfiles/f80d6409-cb1d-4af1-8e1c-1b90f657b9bd/963b770e-595f-4f76-a172-503246d6cf13/aiagents-access/region_time_series_config.json",
    ),
    # Maxlite Client
    "d56a3972-2bfc-4e86-9a02-05d9356b02a5": ClientConfig(
        name="Maxlite",
        s3_athena_output_location="s3://usdplatlakedevbase/computationfiles/d56a3972-2bfc-4e86-9a02-05d9356b02a5/3e21083c-a02e-433f-affc-f4a3f8f797ff/athena-results",
        athena_database="default",
        athena_workgroup="maxlite-ai-agents",
        inventory_replenishment_table="inventory"
    )
}

def get_client_config(company_id: str) -> Optional[ClientConfig]:
    return CLIENT_CONFIGS.get(company_id)
