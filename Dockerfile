FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MINERU_DEVICE_MODE=cpu

# 系统依赖（mineru 运行需要）
RUN apt-get update && apt-get install -y \
    git \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 升级 pip
RUN pip install --upgrade pip

# 官方推荐：直接从 PyPI 安装
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install "mineru[all]" runpod

WORKDIR /app

# 🔥 预热模型缓存（避免冷启动）
RUN mkdir -p /tmp/test && \
    echo "test" > /tmp/test/test.txt && \
    mineru -p /tmp/test/test.txt -o /tmp/output -b pipeline || true

COPY handler.py .

CMD ["python3", "handler.py"]