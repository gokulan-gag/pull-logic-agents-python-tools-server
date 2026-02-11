from app.core.config import settings
import asyncio
import boto3
from typing import Optional, Dict, Any, TypeVar

T = TypeVar('T')

class AthenaClient:
    def __init__(self):
        self.client = boto3.client(
            'athena',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    async def run_query(
        self,
        query: str,
        execution_id: Optional[str] = None,
        next_token: Optional[str] = None,
        max_results: int = 20,
        database: Optional[str] = None,
        output_location: Optional[str] = None,
        workgroup: Optional[str] = None
    ) -> Dict[str, Any]:
        
        # Use provided values or fall back to instance defaults
        db = database
        out_loc = output_location
        wg = workgroup

        try:
            if not execution_id:
                response = self.client.start_query_execution(
                    QueryString=query,
                    QueryExecutionContext={'Database': db},
                    ResultConfiguration={'OutputLocation': out_loc},
                    WorkGroup=wg
                )
                execution_id = response['QueryExecutionId']
                if not execution_id:
                    raise Exception("Failed to start query execution")

            if not next_token:
                state = 'RUNNING'
                while state in ['RUNNING', 'QUEUED']:
                    response = self.client.get_query_execution(QueryExecutionId=execution_id)
                    state = response['QueryExecution']['Status']['State']
                    
                    if state in ['FAILED', 'CANCELLED']:
                        error_msg = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                        raise Exception(f"Athena query failed or was cancelled: {error_msg}")
                    
                    if state == 'SUCCEEDED':
                        break
                    
                    await asyncio.sleep(2)

            kwargs = {
                'QueryExecutionId': execution_id,
                'MaxResults': max_results
            }
            if next_token:
                kwargs['NextToken'] = next_token

            results = self.client.get_query_results(**kwargs)
            
            result_set = results.get('ResultSet', {})
            rows = result_set.get('Rows', [])
            new_next_token = results.get('NextToken')

            if not rows:
                return {
                    'results': [],
                    'executionId': execution_id,
                    'nextToken': None,
                    'hasMore': False
                }

            column_info = result_set.get('ResultSetMetadata', {}).get('ColumnInfo', [])
            headers = [col.get('Name', '') for col in column_info]

            start_index = 1 if not next_token else 0
            data = []
            for row in rows[start_index:]:
                data_row = row.get('Data', [])
                item = {}
                for i, col in enumerate(data_row):
                    if i < len(headers):
                        item[headers[i]] = col.get('VarCharValue')
                data.append(item)

            return {
                'results': data,
                'executionId': execution_id,
                'nextToken': new_next_token,
                'hasMore': bool(new_next_token)
            }

        except Exception as e:
            print(f"Athena query error: {str(e)}")
            raise Exception(f"Athena query failed: {str(e)}")

athena_client = AthenaClient()
