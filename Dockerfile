FROM python:3.10

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MINERU_DEVICE_MODE=cpu
ENV MINERU_MODEL_SOURCE=local

# 系统依赖
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

# 升级 pip
RUN pip install --upgrade pip

# 先装 CPU torch，再装 mineru[core]（官方推荐）
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "mineru[core]>=2.7.0" runpod --only-binary colorlog && \
    pip cache purge

# 预下载模型（官方方式）
RUN mineru-models-download -s huggingface -m all

WORKDIR /app

COPY handler.py .

CMD ["python3", "handler.py"]
