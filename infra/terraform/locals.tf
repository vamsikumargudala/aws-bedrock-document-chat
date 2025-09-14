locals {
  project_prefix = var.project_prefix
  environment    = var.environment

  common_tags = {
    Project     = var.project_prefix
    Environment = var.environment
    ManagedBy   = "Terraform"
    Application = "PersonalRAG"
  }

  # Resource naming convention
  s3_bucket_name     = "${local.project_prefix}-${local.environment}-rag-documents"
  knowledge_base_name = "${local.project_prefix}-${local.environment}-knowledge-base"
  iam_role_name      = "${local.project_prefix}-${local.environment}-bedrock-kb-role"

  # Bedrock configuration
  embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
}