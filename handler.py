import base64
import os
import shutil
import tempfile

import runpod

from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.data_reader_writer import FileBasedDataWriter
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze


def handler(event):
    try:
        pdf_b64 = event["input"]["pdf_base64"]
    except (KeyError, TypeError):
        return {"error": "Missing required field: pdf_base64"}

    work_dir = tempfile.mkdtemp(dir="/tmp")
    try:
        image_dir = os.path.join(work_dir, "images")
        os.makedirs(image_dir)

        pdf_bytes = base64.b64decode(pdf_b64)
        ds = PymuDocDataset(pdf_bytes)
        image_writer = FileBasedDataWriter(image_dir)

        if ds.classify() == SupportedPdfParseMethod.OCR:
            infer_result = ds.apply(doc_analyze, ocr=True)
            pipe_result = infer_result.pipe_ocr_mode(image_writer)
        else:
            infer_result = ds.apply(doc_analyze, ocr=False)
            pipe_result = infer_result.pipe_txt_mode(image_writer)

        markdown = pipe_result.get_markdown(image_dir)
        return {"markdown": markdown}

    except Exception as exc:
        return {"error": str(exc)}

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


runpod.serverless.start({"handler": handler})
