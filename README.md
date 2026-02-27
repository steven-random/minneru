# mineru-serverless

RunPod Serverless worker: PDF (base64) → MinerU → Markdown.

Uses the MinerU CLI with `hybrid-auto-engine` backend. Model weights are
downloaded automatically on first cold start and cached in the container's
ephemeral storage.

## Input

```json
{
  "input": {
    "pdf_base64": "<base64-encoded PDF bytes>"
  }
}
```

## Output

```json
{
  "markdown": "<extracted markdown content>"
}
```

## Build and push

```bash
docker build -t yourdockerhub/mineru-serverless .
docker push yourdockerhub/mineru-serverless
```

## RunPod Serverless setup

1. Push the image to Docker Hub (or any public/private registry).
2. Go to [RunPod Serverless](https://www.runpod.io/console/serverless).
3. Click **New Endpoint**.
4. Set **Container Image** to `yourdockerhub/mineru-serverless`.
5. Set **Container Disk** to at least 20 GB (model weights cache).
6. Select a GPU with CUDA 12.1+ support (A4000 or better recommended).
7. Deploy.

## Cold start note

The first invocation per worker downloads MinerU model weights (~5–10 GB)
from HuggingFace. Subsequent requests on the same worker are fast. Set
**Min Workers** to 1 in the RunPod endpoint settings to keep a worker warm
and avoid repeated downloads.
