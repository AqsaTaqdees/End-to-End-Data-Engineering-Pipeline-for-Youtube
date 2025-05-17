# Import necessary libraries
import awswrangler as wr           # AWS Data Wrangler for easier interaction with AWS services
import pandas as pd               # Pandas for data manipulation
import urllib.parse               # To decode the S3 object key
import os                         # To access environment variables

# Retrieve environment variables set in Lambda configuration
os_input_s3_cleansed_layer = os.environ['s3_cleansed_layer']               # Target S3 path to write cleansed data
os_input_glue_catalog_db_name = os.environ['glue_catalog_db_name']         # Glue catalog database name
os_input_glue_catalog_table_name = os.environ['glue_catalog_table_name']   # Glue catalog table name
os_input_write_data_operation = os.environ['write_data_operation']         # Write mode (e.g., overwrite, append)

# Lambda handler function triggered by S3 event
def lambda_handler(event, context):
    # Extract bucket and object key from the S3 event trigger
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

    try:
        # Read JSON file from S3 and load it into a DataFrame
        df_raw = wr.s3.read_json(f's3://{bucket}/{key}')

        # Normalize the nested 'items' JSON field into a flat DataFrame
        df_step_1 = pd.json_normalize(df_raw['items'])

        # Write the cleansed DataFrame to S3 in Parquet format,
        # and register/update it in the AWS Glue Data Catalog
        wr_response = wr.s3.to_parquet(
            df=df_step_1,
            path=os_input_s3_cleansed_layer,
            dataset=True,
            database=os_input_glue_catalog_db_name,
            table=os_input_glue_catalog_table_name,
            mode=os_input_write_data_operation
        )

        # Return the AWS Wrangler write response for logging or debugging
        return wr_response

    except Exception as e:
        # Print error details if the process fails
        print(e)
        print(f'Error getting object {key} from bucket {bucket}. '
              'Make sure they exist and your bucket is in the same region as this function.')
        raise e
