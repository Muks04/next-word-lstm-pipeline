# ECR repo for Lambda container image
resource "aws_ecr_repository" "lambda" {
  name         = "${var.project_name}-lambda"
  force_delete = true
}

# IAM role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3" {
  name = "s3-model-read"
  role = aws_iam_role.lambda.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.models.arn}/models/*"
    }]
  })
}

# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "inference" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.inference.id
  name        = "$default"
  auto_deploy = true
}

# Lambda + API Gateway integration — only created after image is pushed to ECR
# To enable: push image first, then run terraform apply -var="deploy_lambda=true"
resource "aws_lambda_function" "inference" {
  count         = var.deploy_lambda ? 1 : 0
  function_name = "${var.project_name}-inference"
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:latest"
  timeout       = 60
  memory_size   = 1024

  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.models.bucket
      MODEL_KEY     = "models/next_word_lstm_model_with_early_stopping.h5"
      TOKENIZER_KEY = "models/tokenizer.pickle"
    }
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  count                  = var.deploy_lambda ? 1 : 0
  api_id                 = aws_apigatewayv2_api.inference.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.inference[0].invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "predict" {
  count     = var.deploy_lambda ? 1 : 0
  api_id    = aws_apigatewayv2_api.inference.id
  route_key = "POST /predict"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_lambda_permission" "apigw" {
  count         = var.deploy_lambda ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.inference.execution_arn}/*/*"
}
