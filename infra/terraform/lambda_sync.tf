# Lambda function for syncing Knowledge Base
# Only create these resources when knowledge_base_id is provided
resource "aws_iam_role" "kb_sync_lambda_role" {
  count = var.knowledge_base_id != "" ? 1 : 0
  name = "${local.project_prefix}-${local.environment}-kb-sync-lambda-role"
  tags = local.common_tags

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "kb_sync_lambda_basic" {
  count      = var.knowledge_base_id != "" ? 1 : 0
  role       = aws_iam_role.kb_sync_lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Policy for Lambda to trigger Knowledge Base sync
resource "aws_iam_policy" "kb_sync_lambda_policy" {
  count = var.knowledge_base_id != "" ? 1 : 0
  name = "${local.project_prefix}-${local.environment}-kb-sync-lambda-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:StartIngestionJob",
          "bedrock:GetIngestionJob",
          "bedrock:ListIngestionJobs"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "kb_sync_lambda_bedrock" {
  count      = var.knowledge_base_id != "" ? 1 : 0
  role       = aws_iam_role.kb_sync_lambda_role[0].name
  policy_arn = aws_iam_policy.kb_sync_lambda_policy[0].arn
}

# Lambda function code
resource "aws_lambda_function" "kb_sync" {
  count            = var.knowledge_base_id != "" ? 1 : 0
  filename         = "${path.module}/lambda_sync.zip"
  function_name    = "${local.project_prefix}-${local.environment}-kb-sync"
  role            = aws_iam_role.kb_sync_lambda_role[0].arn
  handler         = "index.handler"
  runtime         = "python3.11"
  timeout         = 60
  tags            = local.common_tags

  environment {
    variables = {
      KNOWLEDGE_BASE_ID = var.knowledge_base_id
      DATA_SOURCE_ID    = var.data_source_id
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.kb_sync_lambda_basic[0],
    aws_iam_role_policy_attachment.kb_sync_lambda_bedrock[0]
  ]
}

# EventBridge rule for scheduled sync (every hour)
resource "aws_cloudwatch_event_rule" "kb_sync_schedule" {
  count               = var.knowledge_base_id != "" ? 1 : 0
  name                = "${local.project_prefix}-${local.environment}-kb-sync-schedule"
  description         = "Trigger Knowledge Base sync every hour"
  schedule_expression = "rate(1 hour)"
  tags               = local.common_tags
}

# EventBridge target
resource "aws_cloudwatch_event_target" "kb_sync_target" {
  count     = var.knowledge_base_id != "" ? 1 : 0
  rule      = aws_cloudwatch_event_rule.kb_sync_schedule[0].name
  target_id = "KBSyncLambda"
  arn       = aws_lambda_function.kb_sync[0].arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  count         = var.knowledge_base_id != "" ? 1 : 0
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.kb_sync[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.kb_sync_schedule[0].arn
}