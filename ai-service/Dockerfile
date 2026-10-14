# CV Screening AI Service — production image (CPU torch)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# CPU torch first; strip torch from requirements to avoid CUDA wheel reinstall
RUN grep -vE '^torch([>=<]|$)' requirements.txt > /tmp/reqs.txt \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r /tmp/reqs.txt

COPY app ./app
COPY models ./models
COPY training ./training

# Fail the build if NER weights are missing (gitignored — must be present on build host)
RUN test -f models/extraction/ner_model/ner/model \
    || (echo "ERROR: models/extraction/ner_model/ner/model missing. Train with: python -m training.train_ner" && exit 1)

ENV HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false \
    LOG_LEVEL=INFO \
    NER_MODEL_PATH=models/extraction/ner_model \
    RANKING_MODEL_PATH=models/ranking \
    EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
  CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
