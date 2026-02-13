import pandas as pd
import boto3
import io
import json
from app.lib.logger import log
from app.core.config import settings

class S3Client:
    """
    S3 Client for reading and writing files from/to AWS S3 using boto3.
    """
    def __init__(self):
        self.region = settings.AWS_REGION
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        
    def read_parquet(self, bucket: str, key: str) -> pd.DataFrame:
        """
        Reads a parquet file from S3 using boto3 and returns a pandas DataFrame.
        """
        try:
            log.info(f"Reading parquet from s3://{bucket}/{key} using boto3")
            
            response = self.client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Use io.BytesIO to read the bytes into pandas
            df = pd.read_parquet(io.BytesIO(content))
            
            log.info(f"Successfully read parquet with {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error reading parquet from s3://{bucket}/{key}: {str(e)}")
            raise e
    
    def read_json(self, bucket: str, key: str) -> pd.DataFrame:
        """
        Reads a json file from S3 using boto3 and returns a pandas DataFrame.
        """
        try:
            log.info(f"Reading json from s3://{bucket}/{key} using boto3")
            
            response = self.client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Use io.BytesIO to read the bytes into pandas
            df = pd.read_json(io.BytesIO(content))
            
            log.info(f"Successfully read json with {len(df)} rows")
            return df
        except Exception as e:
            log.error(f"Error reading json from s3://{bucket}/{key}: {str(e)}")
            raise e

    def read_json_as_dict(self, bucket: str, key: str) -> dict:
        """
        Reads a json file from S3 using boto3 and returns a dictionary.
        """
        try:            
            response = self.client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            data = json.loads(content)
            
            return data
        except Exception as e:
            log.error(f"Error reading json from s3://{bucket}/{key}: {str(e)}")
            raise e

# Singleton instance
s3_client = S3Client()
