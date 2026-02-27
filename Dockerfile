FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    HOME=/root

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3-pip \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

RUN uv pip install --system \
    "torch>=2.1.0" torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

RUN uv pip install --system "mineru[all]" runpod

ARG HF_TOKEN=""
ENV HF_TOKEN=${HF_TOKEN}

RUN python3 -c "\
from huggingface_hub import snapshot_download; \
snapshot_download( \
    repo_id='opendatalab/PDF-Extract-Kit-1.0', \
    local_dir='/opt/models/PDF-Extract-Kit-1.0', \
    ignore_patterns=['*.git*', 'README*', 'LICENSE*'] \
); \
snapshot_download( \
    repo_id='hantian/layoutreader', \
    local_dir='/opt/models/layoutreader', \
    ignore_patterns=['*.git*', 'README*'] \
)"

RUN python3 -c "\
import json; \
config = { \
    'bucket_info': {}, \
    'models-dir': '/opt/models/PDF-Extract-Kit-1.0/models', \
    'layoutreader-model-dir': '/opt/models/layoutreader', \
    'device-mode': 'cuda', \
    'layout-config': {'model': 'layoutlmv3'}, \
    'formula-config': { \
        'mfd_model': 'yolo_v8_mfd', \
        'mfr_model': 'unimernet_small', \
        'enable': True \
    }, \
    'table-config': { \
        'model': 'rapid_table', \
        'enable': True, \
        'max_time': 400 \
    } \
}; \
open('/root/magic-pdf.json', 'w').write(json.dumps(config, indent=2))"

RUN python3 -c "\
from magic_pdf.config.enums import SupportedPdfParseMethod; \
from magic_pdf.data.data_reader_writer import FileBasedDataWriter; \
from magic_pdf.data.dataset import PymuDocDataset; \
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze; \
print('MinerU import validation passed')"

WORKDIR /app
COPY handler.py .

CMD ["python3", "handler.py"]
