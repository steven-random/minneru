"""
Test script for the MinerU RunPod Serverless endpoint.

Quickstart:
    cp .env.example .env   # fill in your values
    python test_endpoint.py

Override via flags:
    python test_endpoint.py --pdf doc.pdf --endpoint <ID> --api-key <KEY>
"""

import argparse
import base64
import os
import sys
import time

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

RUNPOD_BASE_URL = "https://api.runpod.ai/v2"
TIMEOUT = 3600  # 1 hour (HTTP connection timeout)


def encode_pdf(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def submit_job(endpoint_id: str, api_key: str, payload: dict) -> str:
    """Submit async job and return job ID."""
    url = f"{RUNPOD_BASE_URL}/{endpoint_id}/run"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"input": payload},
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
    output = result.get("output", result)

    if "error" in output:
        print(f"\n[FAIL] {output['error']}")
        if output.get("stderr"):
            print(f"\nSTDERR (last 2000 chars):\n{output['stderr']}")
        if output.get("output_files"):
            print(f"\nFiles in output dir: {output['output_files']}")
        sys.exit(1)

    markdown = output.get("markdown", "")
    pages = output.get("pages", "?")
    files = output.get("output_files", [])

    print(f"\n[OK] Got markdown ({len(markdown)} chars, {pages} page(s), {len(files)} files)")
    print("-" * 60)
    print(markdown[:500] + ("..." if len(markdown) > 500 else ""))
    print("-" * 60)

    if save_to:
        with open(save_to, "w", encoding="utf-8") as f:
            f.write(markdown)
        print(f"\nSaved to: {save_to}")


def main():
    parser = argparse.ArgumentParser(description="Test MinerU RunPod endpoint")
    parser.add_argument("--pdf", default=os.environ.get("TEST_PDF"),
                        help="Path to the PDF file")
    parser.add_argument("--endpoint", default=os.environ.get("RUNPOD_ENDPOINT_ID"),
                        help="RunPod Endpoint ID")
    parser.add_argument("--api-key", default=os.environ.get("RUNPOD_API_KEY"),
                        help="RunPod API key")
    parser.add_argument("--save", metavar="FILE",
                        default=os.environ.get("SAVE_OUTPUT") or None,
                        help="Save markdown output to file")
    args = parser.parse_args()

    for name, val in [("RUNPOD_ENDPOINT_ID", args.endpoint),
                      ("RUNPOD_API_KEY", args.api_key),
                      ("TEST_PDF", args.pdf)]:
        if not val:
            print(f"Error: set {name} in .env or pass --{name.lower().replace('_', '-')}")
            sys.exit(1)

    if not os.path.isfile(args.pdf):
        print(f"Error: file not found: {args.pdf}")
        sys.exit(1)

    # encode
    print(f"Encoding: {args.pdf}")
    pdf_b64 = encode_pdf(args.pdf)
    size_mb = len(pdf_b64) * 3 / 4 / 1024 / 1024
    print(f"  Size: {size_mb:.1f} MB (base64: {len(pdf_b64)} chars)")

    # submit + poll
    payload = {"pdf_base64": pdf_b64}
    print("\nSubmitting job...")
    job_id = submit_job(args.endpoint, args.api_key, payload)
    print(f"  Job ID: {job_id}")
    print("Polling for result...")
    result = poll_status(args.endpoint, args.api_key, job_id)

    print_result(result, save_to=args.save)


if __name__ == "__main__":
    main()
