# IAM Role for Bedrock Knowledge Base
resource "aws_iam_role" "bedrock_kb_role" {
  name = local.iam_role_name
  tags = local.common_tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# IAM Policy for S3 Access
resource "aws_iam_policy" "bedrock_kb_s3_policy" {
  name = "${local.project_prefix}-${local.environment}-bedrock-s3-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.rag_documents.arn,
          "${aws_s3_bucket.rag_documents.arn}/*"
        ]
      }
    ]
  })
}

# IAM Policy for Bedrock Model Access
resource "aws_iam_policy" "bedrock_kb_model_policy" {
  name = "${local.project_prefix}-${local.environment}-bedrock-model-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = local.embedding_model_arn
      }
    ]
  })
}

# Attach policies to role
resource "aws_iam_role_policy_attachment" "bedrock_kb_s3" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "bedrock_kb_model" {
  role       = aws_iam_role.bedrock_kb_role.name
  policy_arn = aws_iam_policy.bedrock_kb_model_policy.arn
}

# Data for current AWS account
data "aws_caller_identity" "current" {}

# ============================================================
# MANUAL STEPS AFTER TERRAFORM APPLY:
# ============================================================
# 1. Go to AWS Console > Amazon Bedrock > Knowledge bases
# 2. Click "Create knowledge base"
# 3. Configure:
#    - Name: Use the same as local.knowledge_base_name
#    - IAM Role: Select the role created above
#    - Data Source: S3 bucket created by this Terraform
#    - Embeddings Model: Titan Text Embeddings v2
#    - Vector Database: Amazon S3 Vectors
# 4. Save the Knowledge Base ID for use in .env file
# ============================================================