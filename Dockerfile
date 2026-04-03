# Force linux/amd64 platform — required for tensorflow-cpu on Apple Silicon
FROM --platform=linux/amd64 public.ecr.aws/docker/library/python:3.10-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app and model files
COPY app1.py model.py ./
COPY next_word_lstm_model_with_early_stopping.h5 ./
COPY tokenizer.pickle ./

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app1.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
