"""
Test script for the MinerU RunPod Serverless endpoint.

Quickstart:
    python test_endpoint.py

Or override via flags:
    python test_endpoint.py --pdf your_file.pdf --endpoint <ID> --api-key <KEY>
"""

import argparse
import base64
import os
import sys
import time

import requests

# Load .env if present (requires: pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RUNPOD_BASE_URL = "https://api.runpod.ai/v2"


def encode_pdf(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


TIMEOUT = 3600  # 1 hour

def run_sync(endpoint_id: str, api_key: str, pdf_b64: str) -> dict:
    url = f"{RUNPOD_BASE_URL}/{endpoint_id}/runsync"
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={"input": {"pdf_base64": pdf_b64}},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def run_async(endpoint_id: str, api_key: str, pdf_b64: str) -> str:
    """Submit job and return job ID."""
    url = f"{RUNPOD_BASE_URL}/{endpoint_id}/run"
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={"input": {"pdf_base64": pdf_b64}},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def poll_status(endpoint_id: str, api_key: str, job_id: str, poll_interval: int = 5) -> dict:
    url = f"{RUNPOD_BASE_URL}/{endpoint_id}/status/{job_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    while True:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")

        print(f"  Status: {status}")

        if status == "COMPLETED":
            return data
        if status in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Job {status}: {data}")

        time.sleep(poll_interval)


def print_result(result: dict, save_to: str | None = None):
    output = result.get("output", result)  # runsync wraps in "output"

    if "error" in output:
        print(f"\n[FAIL] Error from worker:\n  {output['error']}")
        sys.exit(1)

    markdown = output.get("markdown", "")
    preview = markdown[:500] + ("..." if len(markdown) > 500 else "")
    print(f"\n[OK] Got markdown ({len(markdown)} chars)")
    print("-" * 60)
    print(preview)
    print("-" * 60)

    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"\nFull output saved to: {save_to}")


def main():
    parser = argparse.ArgumentParser(description="Test MinerU RunPod endpoint")
    parser.add_argument("--pdf", default=os.environ.get("TEST_PDF"), help="Path to the PDF file to upload")
    parser.add_argument("--endpoint", default=os.environ.get("RUNPOD_ENDPOINT_ID"), help="RunPod Endpoint ID")
    parser.add_argument("--api-key", default=os.environ.get("RUNPOD_API_KEY"), help="RunPod API key")
    parser.add_argument("--async-mode", action="store_true",
                        default=os.environ.get("ASYNC_MODE", "false").lower() == "true",
                        help="Use async run + polling instead of runsync")
    parser.add_argument("--save", metavar="FILE", default=os.environ.get("SAVE_OUTPUT") or None,
                        help="Save markdown output to this file")
    args = parser.parse_args()

    if not args.endpoint:
        print("Error: set RUNPOD_ENDPOINT_ID in .env or pass --endpoint")
        sys.exit(1)
    if not args.api_key:
        print("Error: set RUNPOD_API_KEY in .env or pass --api-key")
        sys.exit(1)
    if not args.pdf:
        print("Error: set TEST_PDF in .env or pass --pdf")
        sys.exit(1)
    if not os.path.isfile(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)

    print(f"Encoding PDF: {args.pdf}")
    pdf_b64 = encode_pdf(args.pdf)
    print(f"  Encoded size: {len(pdf_b64)} chars")

    if args.async_mode:
        print("\nSubmitting async job...")
        job_id = run_async(args.endpoint, args.api_key, pdf_b64)
        print(f"  Job ID: {job_id}")
        print("Polling for result...")
        result = poll_status(args.endpoint, args.api_key, job_id)
    else:
        print("\nSending runsync request...")
        result = run_sync(args.endpoint, args.api_key, pdf_b64)

    print_result(result, save_to=args.save)


if __name__ == "__main__":
    main()
