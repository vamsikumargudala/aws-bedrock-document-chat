terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configuration will be provided via backend.tf or -backend-config flags
    # Example:
    # bucket         = "personal-dev-terraform-state"
    # key            = "rag/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "personal-dev-terraform-locks"
    # encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}