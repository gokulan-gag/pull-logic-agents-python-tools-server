from app.lib.athena import athena_client
from typing import Dict, Any
from app.schemas.inventory_analysis import InventoryAnalysisRequestWithSelection
from app.services.inventory_analysis.query_builder_service import query_builder_service
from app.services.inventory_analysis.base import IInventoryAnalysisService
from app.core.client_config import ClientConfig
from app.lib.logger import log

class MaxliteInventoryAnalysisService(IInventoryAnalysisService):
    def __init__(self, config: ClientConfig):
        self.config = config

    async def get_enough_stock(self, request: InventoryAnalysisRequestWithSelection) -> Dict[str, Any]:
        try:
            log.info(f"Request received for inventory analysis: {request}")
            
            # Cast to Selection type if needed, or just pass as is if it's compatible
            query = await query_builder_service.build_query(request, table_name=self.config.inventory_replenishment_table)
            log.info(f"Athena query: {query}")

            data = await athena_client.run_query(
                query=query,
                execution_id=request.executionId,
                next_token=request.nextToken,
                max_results=request.limit or 20,
                database=self.config.athena_database,
                output_location=self.config.s3_athena_output_location,
                workgroup=self.config.athena_workgroup
            )

            results = data['results']
            return {
                "results": results,
                "executionId": data['executionId'],
                "nextToken": data['nextToken'],
                "hasMore": data['hasMore'],
                "count": len(results)
            }
        except Exception as e:
            log.error(f"Error in get_enough_stock: {str(e)}")
            raise Exception(str(e))

    async def get_excess_stock(self, request: InventoryAnalysisRequestWithSelection) -> Dict[str, Any]:
        try:
            log.info(f"Request received for inventory analysis: {request}")
            query = await query_builder_service.build_query(request, table_name=self.config.inventory_replenishment_table)
            log.info(f"Athena query: {query}")

            data = await athena_client.run_query(
                query=query,
                execution_id=request.executionId,
                next_token=request.nextToken,
                max_results=request.limit or 20,
                database=self.config.athena_database,
                output_location=self.config.s3_athena_output_location,
                workgroup=self.config.athena_workgroup
            )

            results = data['results']
            return {
                "results": results,
                "executionId": data['executionId'],
                "nextToken": data['nextToken'],
                "hasMore": data['hasMore'],
                "count": len(results)
            }
        except Exception as e:
            log.error(f"Error in get_excess_stock: {str(e)}")
            raise Exception(str(e))
