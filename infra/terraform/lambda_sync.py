import boto3
import os
import json
from datetime import datetime

def handler(event, context):
    """
    Lambda function to sync Bedrock Knowledge Base with S3 data
    """
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
    data_source_id = os.environ.get('DATA_SOURCE_ID')

    if not knowledge_base_id or not data_source_id:
        print("Error: KNOWLEDGE_BASE_ID and DATA_SOURCE_ID must be set")
        return {
            'statusCode': 400,
            'body': json.dumps('Missing required environment variables')
        }

    bedrock_agent = boto3.client('bedrock-agent')

    try:
        # Start ingestion job
        response = bedrock_agent.start_ingestion_job(
            knowledgeBaseId=knowledge_base_id,
            dataSourceId=data_source_id,
            description=f'Scheduled sync at {datetime.utcnow().isoformat()}'
        )

        ingestion_job_id = response['ingestionJob']['ingestionJobId']
        status = response['ingestionJob']['status']

        print(f"Started ingestion job: {ingestion_job_id}")
        print(f"Status: {status}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Sync started successfully',
                'ingestionJobId': ingestion_job_id,
                'status': status
            })
        }

    except Exception as e:
        print(f"Error starting sync: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }