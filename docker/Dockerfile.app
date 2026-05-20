FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu22.04

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Keep the CUDA-enabled PyTorch stack explicit so later dependency installs do
# not accidentally replace it with a CPU-only wheel.
RUN ln -sf /usr/bin/python3 /usr/local/bin/python \
    && python -m pip install --upgrade pip \
    && python -m pip install \
        --index-url https://download.pytorch.org/whl/cu128 \
        torch==2.8.0 \
        torchvision==0.23.0

COPY backend/requirements.txt ./requirements.txt
RUN python -m pip install -r requirements.txt

COPY backend/app ./app
COPY backend/training ./training
COPY backend/scripts ./scripts
COPY backend/data/dictionary.db ./data/dictionary.db
COPY backend/models ./models

EXPOSE 8000 8011 8012
