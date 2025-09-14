output "s3_bucket_name" {
  description = "Name of the S3 bucket for documents"
  value       = aws_s3_bucket.rag_documents.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.rag_documents.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_kb_role.arn
}

output "iam_role_name" {
  description = "Name of the IAM role for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_kb_role.name
}

output "lambda_function_name" {
  description = "Name of the Lambda sync function"
  value       = var.knowledge_base_id != "" ? aws_lambda_function.kb_sync[0].function_name : "Not created - set knowledge_base_id first"
}

output "next_steps" {
  description = "Instructions for manual steps"
  value = <<-EOT

    ========== NEXT STEPS ==========

    1. Create Knowledge Base in AWS Console:
       - Go to: Amazon Bedrock > Knowledge bases
       - Create new Knowledge Base with:
         * Name: ${local.knowledge_base_name}
         * IAM Role: ${aws_iam_role.bedrock_kb_role.name}
         * S3 Bucket: ${aws_s3_bucket.rag_documents.id}
         * Vector Store: Amazon S3 Vectors

    2. After creating Knowledge Base, update terraform.tfvars:
       knowledge_base_id = "<your-kb-id>"
       data_source_id = "<your-datasource-id>"

    3. Run terraform apply again to create Lambda sync function

    4. Update your .env file with:
       AWS_REGION=${var.aws_region}
       BEDROCK_KNOWLEDGE_BASE_ID=<your-kb-id>
       S3_BUCKET_NAME=${aws_s3_bucket.rag_documents.id}

    ================================
  EOT
}