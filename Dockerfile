FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install mineru runpod torch --index-url https://download.pytorch.org/whl/cpu

WORKDIR /app

# 触发模型下载（关键步骤）
RUN mkdir -p /tmp/test && \
    echo "test" > /tmp/test/test.txt

# 关键：调用一次 pipeline 触发模型缓存
RUN mineru -p /tmp/test/test.txt -o /tmp/output -b pipeline || true

COPY handler.py .

CMD ["python3", "handler.py"]