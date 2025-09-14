variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_prefix" {
  description = "Prefix for all resource names"
  type        = string
  default     = "personal"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID (set after manual creation)"
  type        = string
  default     = ""
}

variable "data_source_id" {
  description = "Bedrock Data Source ID (set after manual creation)"
  type        = string
  default     = ""
}