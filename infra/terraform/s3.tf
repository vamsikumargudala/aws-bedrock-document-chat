resource "aws_s3_bucket" "rag_documents" {
  bucket = local.s3_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_versioning" "rag_documents" {
  bucket = aws_s3_bucket.rag_documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "rag_documents" {
  bucket = aws_s3_bucket.rag_documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "rag_documents" {
  bucket = aws_s3_bucket.rag_documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}