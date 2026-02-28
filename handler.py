import base64
import glob
import os
import shutil
import subprocess
import tempfile

import runpod

WORK_ROOT = os.environ.get("MINERU_WORK_DIR", "/tmp")
BACKEND = os.environ.get("MINERU_BACKEND", "pipeline")


def handler(event):
    inp = event.get("input", {})

    # --- validate input ---
    pdf_b64 = inp.get("pdf_base64")
    if not pdf_b64:
        return {"error": "Missing required field: input.pdf_base64"}

    backend = inp.get("backend", BACKEND)

    work_dir = tempfile.mkdtemp(dir=WORK_ROOT)
    try:
        pdf_path = os.path.join(work_dir, "input.pdf")
        output_dir = os.path.join(work_dir, "output")
        os.makedirs(output_dir)

        # decode PDF
        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(pdf_b64))

        # run MinerU
        result = subprocess.run(
            ["mineru", "-p", pdf_path, "-o", output_dir, "-b", backend],
            capture_output=True,
            text=True,
        )

        # collect output files for debugging
        output_files = []
        for root, _, files in os.walk(output_dir):
            for fname in files:
                output_files.append(os.path.relpath(os.path.join(root, fname), output_dir))

        if result.returncode != 0:
            return {
                "error": f"mineru exited with code {result.returncode}",
                "stderr": result.stderr[-2000:] if result.stderr else "",
                "output_files": output_files,
            }

        # find markdown output
        md_files = glob.glob(os.path.join(output_dir, "**", "*.md"), recursive=True)
        if not md_files:
            return {
                "error": "No markdown output produced",
                "stderr": result.stderr[-2000:] if result.stderr else "",
                "output_files": output_files,
            }

        with open(md_files[0], "r", encoding="utf-8") as f:
            markdown = f.read()

        return {
            "markdown": markdown,
            "pages": len(glob.glob(os.path.join(output_dir, "**", "*.md"), recursive=True)),
            "output_files": output_files,
        }

    except Exception as exc:
        return {"error": str(exc)}

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


runpod.serverless.start({"handler": handler})
