FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MINERU_DEVICE_MODE=cpu

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    fonts-noto-core \
    fonts-noto-cjk \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Pin pip (pip 26+ has resolution-too-deep and colorlog build issues)
RUN pip install pip==24.3.1

# Install CPU PyTorch first, then MinerU
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install "mineru[core]>=2.7.0" runpod && \
    pip cache purge

# Pre-download models during build (avoids cold-start downloads)
RUN mineru-models-download -s huggingface -m all

WORKDIR /app
COPY handler.py .

# Use pre-downloaded models at runtime
ENV MINERU_MODEL_SOURCE=local

CMD ["python3", "handler.py"]
