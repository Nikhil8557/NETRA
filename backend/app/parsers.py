# backend/app/parsers.py
import os
import logging
import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import httpx
from typing import List, Dict, Any
from app.config import settings

logger = logging.getLogger("ksp_netra.parsers")

# CPU/IO heavy tasks are isolated to executor pools to prevent blocking the async loop
process_pool = ProcessPoolExecutor(max_workers=2)
thread_pool = ThreadPoolExecutor(max_workers=4)

def _sync_ocr_file(filepath: str) -> str:
    """Synchronous file-to-string operations executed in ProcessPoolExecutor."""
    _, ext = os.path.splitext(filepath.lower())
    extracted_text = ""
    
    if ext == ".pdf":
        # Convert PDF pages to PIL images cleanly (requires poppler installed system-wide)
        pages = convert_from_path(filepath, dpi=200)
        for page in pages:
            extracted_text += pytesseract.image_to_string(page) + "\n"
    elif ext in [".tiff", ".tif", ".png", ".jpg", ".jpeg"]:
        with Image.open(filepath) as img:
            extracted_text = pytesseract.image_to_string(img)
    else:
        raise ValueError(f"File extension '{ext}' not supported by OCR engine.")
        
    return extracted_text.strip()

async def process_ocr(filepath: str) -> str:
    """Asynchronously schedules OCR conversion inside non-blocking process worker."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source file {filepath} not found.")
    
    logger.info(f"Offloading OCR process for {filepath} to CPU pool...")
    loop = asyncio.get_running_loop()
    try:
        text = await loop.run_in_executor(process_pool, _sync_ocr_file, filepath)
        return text
    except Exception as e:
        logger.error(f"OCR thread processing failed: {e}")
        raise RuntimeError(f"OCR processing engine failed: {e}")

async def translate_kannada_to_english(kannada_text: str) -> str:
    """
    Submits translation workloads directly to a self-hosted IndicTrans2 HTTP server.
    Falls back to defensive local logging on failure.
    """
    logger.info("Routing translation payload to NMT service...")
    payload = {
        "text": kannada_text,
        "source_language": "kannada",
        "target_language": "english"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(settings.INDIC_TRANSLATOR_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("translated_text", "")
    except Exception as e:
        logger.error(f"IndicTrans2 remote translator call failed: {e}. Falling back to default raw text.")
        return f"[Translation Offline Fallback]: {kannada_text}"

def _sync_pandas_cdr(filepath: str) -> List[Dict[str, Any]]:
    """Synchronous Pandas IO execution."""
    df = pd.read_excel(filepath) if filepath.endswith(('.xlsx', '.xls')) else pd.read_csv(filepath)
    df.columns = [str(col).strip().lower() for col in df.columns]
    
    schema_mapping = {
        "calling_no": "caller", "called_no": "receiver", "dialed_no": "receiver",
        "calling_number": "caller", "called_number": "receiver",
        "date_time": "timestamp", "time": "timestamp", "cell_id": "tower_id"
    }
    df = df.rename(columns=schema_mapping)
    target_columns = {"caller", "receiver", "timestamp", "tower_id"}
    missing = target_columns - set(df.columns)
    if missing:
        raise KeyError(f"Standardized headers mapping mismatch: missing {missing}")
        
    edges = []
    for idx, row in df.iterrows():
        edges.append({
            "source": str(row["caller"]).strip(),
            "target": str(row["receiver"]).strip(),
            "timestamp": str(row["timestamp"]),
            "tower_id": str(row["tower_id"]).strip(),
            "duration_sec": int(row["duration"]) if "duration" in row and pd.notna(row["duration"]) else None
        })
    return edges

async def parse_cdr_file(filepath: str) -> List[Dict[str, Any]]:
    """Schedules tabular IO parsing outside the main event loop to avoid thread locks."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CDR target filepath {filepath} is invalid.")
        
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(thread_pool, _sync_pandas_cdr, filepath)
    except Exception as e:
        logger.error(f"CDR parsing operation failed: {e}")
        raise
