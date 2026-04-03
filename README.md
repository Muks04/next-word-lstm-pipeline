# Next Word Prediction — LSTM

Next word prediction app trained on Shakespeare's Hamlet. Built with TensorFlow + Streamlit, deployed on AWS ECS Fargate following the AWS Well-Architected Framework.

## Architecture

```
User → ECS Fargate (Streamlit) → S3 (model store)
              ↓
       CloudWatch Logs
```

## Run Locally

```bash
# With Docker (recommended)
docker-compose up

# Without Docker
pip install -r requirements.txt
streamlit run app1.py
```

## Deploy to AWS

**1. Upload model artifacts to S3**
```bash
aws s3 cp next_word_lstm_model_with_early_stopping.h5 s3://YOUR_BUCKET/models/
aws s3 cp tokenizer.pickle s3://YOUR_BUCKET/models/
```

**2. Provision infrastructure with Terraform**
```bash
cd terraform
terraform init
terraform apply
```

**3. Build and push Docker image to ECR**
```bash
aws ecr get-login-password | docker login --username AWS --password-stdin YOUR_ECR_URL
docker build -t next-word-lstm .
docker tag next-word-lstm:latest YOUR_ECR_URL:latest
docker push YOUR_ECR_URL:latest
```

**4. Force ECS redeployment**
```bash
aws ecs update-service --cluster next-word-lstm-cluster --service next-word-lstm-service --force-new-deployment
```

## Swap Model (Plug and Play)

```bash
# Upload new model to S3
aws s3 cp new_model.h5 s3://YOUR_BUCKET/models/next_word_lstm_model_with_early_stopping.h5

# Redeploy — no code change needed
aws ecs update-service --cluster next-word-lstm-cluster --service next-word-lstm-service --force-new-deployment
```

## CI/CD

Push to `main` branch → GitHub Actions automatically builds, pushes to ECR, and deploys to ECS.

Set these GitHub secrets:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## AWS Well-Architected Pillars

| Pillar | Implementation |
|---|---|
| Operational Excellence | CI/CD via GitHub Actions, IaC via Terraform |
| Security | IAM task roles, private S3, no hardcoded credentials |
| Reliability | ECS auto-restarts, S3 versioning for model rollback |
| Performance | `@st.cache_resource` model caching, Fargate auto-scaling |
| Cost Optimization | Fargate 0.5vCPU/1GB, 7-day log retention, S3 pay-per-use |
| Sustainability | Graviton2 (ARM64) ready, scale-to-zero for dev |
