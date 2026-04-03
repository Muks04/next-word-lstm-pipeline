variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "next-word-lstm"
}

variable "github_owner" {
  description = "Your GitHub username"
  default     = "your-github-username"
}

variable "github_repo" {
  description = "Your GitHub repo name"
  default     = "next-word-prediction-lstm"
}

variable "deploy_lambda" {
  description = "Set to true only after pushing Lambda image to ECR"
  type        = bool
  default     = false
}
