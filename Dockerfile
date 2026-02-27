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

# 用 pip 24.x（pip 26 有 resolution-too-deep 和 colorlog 构建问题）
RUN pip install pip==24.3.1

# 先装 CPU torch，再装 mineru[core]（官方推荐）
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "mineru[core]>=2.7.0" runpod && \
    pip cache purge

# 初始化配置文件 + 预下载模型
RUN echo '{}' > /root/.mineru.json && \
    mineru-models-download -s huggingface -m all

WORKDIR /app

COPY handler.py .

CMD ["python3", "handler.py"]
