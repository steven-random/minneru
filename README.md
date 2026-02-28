# mineru-serverless

RunPod Serverless worker that converts PDF documents to Markdown using [MinerU](https://github.com/opendatalab/MinerU).

## How it works

```
PDF (base64) → RunPod Worker → MinerU pipeline → Markdown
```

The worker receives a base64-encoded PDF, runs MinerU's `pipeline` backend, and returns the extracted Markdown text.

## API

### Input

```json
{
  "input": {
    "pdf_base64": "<base64-encoded PDF>"
  }
}
```

### Output (success)

```json
{
  "markdown": "# Extracted content...",
  "pages": 1,
  "output_files": ["input/input.md", "input/images/fig1.png"]
}
```

### Output (error)

```json
{
  "error": "description of what went wrong",
  "stderr": "...",
  "output_files": []
}
```

## Deploy

### 1. Build and push the Docker image

```bash
docker build -t <your-registry>/mineru-serverless .
docker push <your-registry>/mineru-serverless
```

### 2. Create a RunPod Serverless endpoint

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint**
3. Set **Container Image** to your pushed image
4. Set **Container Disk** to at least **20 GB** (model weights are baked into the image)
5. Deploy

## Test

### Setup

```bash
pip install requests python-dotenv
cp .env.example .env
# Edit .env with your endpoint ID, API key, and PDF path
```

### Run

```bash
# Uses settings from .env
python test_endpoint.py

# Or pass arguments directly
python test_endpoint.py --pdf document.pdf --endpoint <ID> --api-key <KEY>

# Save output to file
python test_endpoint.py --save output.md
```

## Configuration

### Environment variables (container)

| Variable | Default | Description |
|---|---|---|
| `MINERU_DEVICE_MODE` | `cpu` | Device mode (`cpu` or `cuda`) |
| `MINERU_MODEL_SOURCE` | `local` | Model source (`local` uses pre-downloaded models) |
| `MINERU_BACKEND` | `pipeline` | MinerU backend |
| `MINERU_WORK_DIR` | `/tmp` | Temporary working directory |

### Environment variables (test script)

| Variable | Flag | Description |
|---|---|---|
| `RUNPOD_ENDPOINT_ID` | `--endpoint` | RunPod endpoint ID |
| `RUNPOD_API_KEY` | `--api-key` | RunPod API key |
| `TEST_PDF` | `--pdf` | Path to test PDF file |
| `SAVE_OUTPUT` | `--save` | Save markdown to file |

## Project structure

```
.
├── Dockerfile           # Container image (python:3.10 + MinerU CPU)
├── handler.py           # RunPod serverless handler
├── test_endpoint.py     # Test script
├── .env.example         # Environment variable template
├── .gitignore
└── README.md
```

## Notes

- **CPU-only**: This image uses CPU PyTorch (~900MB base) instead of the official GPU image (~10GB+). Processing is slower but the image is much smaller.
- **Models pre-downloaded**: Model weights (~5GB) are downloaded during `docker build`, so there is no cold-start download delay.
- **pip pinned to 24.x**: pip 26+ has dependency resolution issues with MinerU's dependencies.
