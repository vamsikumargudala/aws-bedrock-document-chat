# Infrastructure Setup

This Terraform configuration sets up the necessary AWS resources for a Bedrock Knowledge Base with S3 Vectors.

## What Gets Deployed

### Phase 1 (Initial Deploy):
- **S3 Bucket**: Stores your documents with encryption and versioning
- **IAM Role**: For Bedrock Knowledge Base to access S3 and embedding models
- **IAM Policies**: Proper permissions for S3 access and model invocation

### Phase 2 (After Manual KB Creation):
- **Lambda Function**: Syncs Knowledge Base with S3 documents
- **EventBridge Rule**: Triggers sync every hour automatically

## Deployment Steps

### 1. Setup Terraform Backend
```bash
./setup-backend.sh
```

### 2. Package Lambda Function
```bash
./package_lambda.sh
```

### 3. Deploy Phase 1 Resources
```bash
terraform init -backend-config=backend.tf
terraform plan
terraform apply
```

### 4. Create Knowledge Base Manually
Go to AWS Console > Amazon Bedrock > Knowledge bases:
- Click "Create knowledge base"
- Use the IAM role name from Terraform output
- Select S3 bucket from Terraform output
- Choose "Amazon S3 Vectors" as vector store
- Select "Titan Text Embeddings v2" model
- Save the Knowledge Base ID and Data Source ID

### 5. Deploy Phase 2 (Lambda Sync)
Update `terraform.tfvars`:
```hcl
knowledge_base_id = "YOUR_KB_ID"
data_source_id    = "YOUR_DATASOURCE_ID"
```

Then apply:
```bash
terraform apply
```

## Auto-Sync Schedule

The Lambda function will automatically sync your S3 documents with the Knowledge Base every hour. You can adjust the schedule in `lambda_sync.tf` by modifying the `schedule_expression`.

## Manual Sync

To trigger a manual sync, invoke the Lambda function:
```bash
aws lambda invoke --function-name personal-dev-kb-sync response.json
```