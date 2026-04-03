output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.models.bucket
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "lambda_api_url" {
  value = "${aws_apigatewayv2_stage.default.invoke_url}/predict"
}

output "pipeline_name" {
  value = aws_codepipeline.mlops.name
}

output "github_connection_arn" {
  value       = aws_codestarconnections_connection.github.arn
  description = "Complete GitHub connection setup in AWS Console before first pipeline run"
}
