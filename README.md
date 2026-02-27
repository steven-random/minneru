# mineru-serverless

RunPod Serverless worker: PDF (base64) → MinerU → Markdown.

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

## Build

```bash
docker build -t mineru-serverless .
# With a HuggingFace token (required for gated models):
docker build --build-arg HF_TOKEN=hf_xxx -t mineru-serverless .
```

## Deploy

1. Push the image to a container registry accessible by RunPod.
2. Create a RunPod Serverless endpoint pointing to the image.
3. Set container disk to at least 20GB to accommodate model weights.
4. Attach a GPU with CUDA 12.1+ support (A4000 or better recommended).

## Notes

- The Docker image is large (~12–15 GB) due to embedded model weights.
- Model weights are downloaded from HuggingFace at build time into the image layer, eliminating cold-start model fetching.
- The first invocation per worker will incur CUDA initialization overhead (~10–30s depending on GPU).
- Temporary files are written to `/tmp` and cleaned up after every request.
- Images extracted from the PDF are discarded; only the markdown text is returned.
