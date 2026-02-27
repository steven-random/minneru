import base64
import glob
import os
import shutil
import subprocess
import tempfile

import runpod


def handler(event):
    try:
        pdf_b64 = event["input"]["pdf_base64"]
    except (KeyError, TypeError):
        return {"error": "Missing required field: pdf_base64"}

    work_dir = tempfile.mkdtemp(dir="/tmp")
    try:
        pdf_path = os.path.join(work_dir, "input.pdf")
        output_dir = os.path.join(work_dir, "output")
        os.makedirs(output_dir)

        with open(pdf_path, "wb") as f:
            f.write(base64.b64decode(pdf_b64))

        result = subprocess.run(
            ["mineru", "-p", pdf_path, "-o", output_dir, "-b", "pipeline"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            return {"error": result.stderr or "mineru process failed",
                    "stdout": result.stdout}

        # 列出输出目录所有文件，方便调试
        all_files = []
        for root, _, files in os.walk(output_dir):
            for f in files:
                all_files.append(os.path.relpath(os.path.join(root, f), output_dir))

        md_files = glob.glob(os.path.join(output_dir, "**", "*.md"), recursive=True)
        if not md_files:
            return {"error": "No markdown output produced",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "output_files": all_files}

        with open(md_files[0], "r", encoding="utf-8") as f:
            markdown = f.read()

        return {"markdown": markdown}

    except Exception as exc:
        return {"error": str(exc)}

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


runpod.serverless.start({"handler": handler})
