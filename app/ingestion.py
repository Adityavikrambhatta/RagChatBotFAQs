from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf", ".txt", ".md"}
LIKELY_ERROR_COLUMNS = ("error", "exception", "message", "issue", "problem", "code")
LIKELY_RESOLUTION_COLUMNS = ("resolution", "fix", "workaround", "action", "solution", "steps")


@dataclass(slots=True)
class ChunkRecord:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    normalized = normalize_text(text)
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(normalized)
    while start < text_length:
        end = min(start + chunk_size, text_length)
        window = normalized[start:end]
        if end < text_length:
            last_break = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("; "))
            if last_break > int(chunk_size * 0.55):
                end = start + last_break + 1
                window = normalized[start:end]
        chunk = window.strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def infer_primary_columns(columns: list[str]) -> dict[str, str | None]:
    lowered = {column.lower(): column for column in columns}

    preferred_error_order = (
        "error_message",
        "message",
        "error text",
        "exception_message",
        "issue",
        "problem",
    )
    error_col = next((lowered[key] for key in preferred_error_order if key in lowered), None)
    if error_col is None:
        error_col = next(
            (
                original
                for key, original in lowered.items()
                if any(token in key for token in LIKELY_ERROR_COLUMNS) and "code" not in key
            ),
            None,
        )

    resolution_col = next(
        (original for key, original in lowered.items() if any(token in key for token in LIKELY_RESOLUTION_COLUMNS)),
        None,
    )
    preferred_code_order = ("error_code", "code", "exception_code")
    code_col = next((lowered[key] for key in preferred_code_order if key in lowered), None)
    if code_col is None:
        code_col = next((original for key, original in lowered.items() if "code" in key), None)
    return {"error": error_col, "resolution": resolution_col, "code": code_col}


def row_to_text(row: dict[str, Any], primary_columns: dict[str, str | None]) -> str:
    lines: list[str] = []
    if primary_columns["code"] and row.get(primary_columns["code"]):
        lines.append(f"Error code: {row[primary_columns['code']]}")
    if primary_columns["error"] and row.get(primary_columns["error"]):
        lines.append(f"Error message: {row[primary_columns['error']]}")
    if primary_columns["resolution"] and row.get(primary_columns["resolution"]):
        lines.append(f"Resolution: {row[primary_columns['resolution']]}")

    for key, value in row.items():
        if value in ("", None):
            continue
        if isinstance(value, float) and pd.isna(value):
            continue
        if key in primary_columns.values():
            continue
        label = key.replace("_", " ").strip().title()
        lines.append(f"{label}: {value}")
    return "\n".join(lines)


def dataframe_to_records(dataframe: pd.DataFrame, *, source_file: Path, sheet_name: str | None) -> list[ChunkRecord]:
    frame = dataframe.fillna("")
    normalized_columns = [str(column).strip() for column in frame.columns]
    frame.columns = normalized_columns
    primary_columns = infer_primary_columns(normalized_columns)
    records: list[ChunkRecord] = []

    for row_index, (_, series) in enumerate(frame.iterrows(), start=1):
        row = {str(key): value for key, value in series.to_dict().items()}
        text = normalize_text(row_to_text(row, primary_columns))
        if not text:
            continue
        record_id = f"{source_file.stem}-{sheet_name or 'sheet'}-row-{row_index}"
        metadata = {
            "source_file": source_file.name,
            "source_path": str(source_file),
            "source_type": "tabular_row",
            "sheet_name": sheet_name or "",
            "row_number": row_index,
            "error_message": row.get(primary_columns["error"]) if primary_columns["error"] else "",
            "error_code": row.get(primary_columns["code"]) if primary_columns["code"] else "",
            "resolution": row.get(primary_columns["resolution"]) if primary_columns["resolution"] else "",
        }
        records.append(ChunkRecord(chunk_id=record_id, text=text, metadata=metadata))
    return records


def load_tabular_file(path: Path) -> list[ChunkRecord]:
    if path.suffix.lower() == ".csv":
        dataframe = pd.read_csv(path)
        return dataframe_to_records(dataframe, source_file=path, sheet_name=None)

    workbook = pd.read_excel(path, sheet_name=None)
    records: list[ChunkRecord] = []
    for sheet_name, dataframe in workbook.items():
        records.extend(dataframe_to_records(dataframe, source_file=path, sheet_name=str(sheet_name)))
    return records


def load_pdf_file(path: Path, *, chunk_size: int, chunk_overlap: int) -> list[ChunkRecord]:
    reader = PdfReader(str(path))
    records: list[ChunkRecord] = []
    for page_number, page in enumerate(reader.pages, start=1):
        raw = normalize_text(page.extract_text() or "")
        if not raw:
            continue
        for index, chunk in enumerate(chunk_text(raw, chunk_size=chunk_size, chunk_overlap=chunk_overlap)):
            chunk_id = f"{path.stem}-page-{page_number}-{index}"
            metadata = {
                "source_file": path.name,
                "source_path": str(path),
                "source_type": "pdf_page",
                "page_number": page_number,
            }
            records.append(ChunkRecord(chunk_id=chunk_id, text=chunk, metadata=metadata))
    return records


def load_text_file(path: Path, *, chunk_size: int, chunk_overlap: int) -> list[ChunkRecord]:
    text = normalize_text(path.read_text(encoding="utf-8"))
    records: list[ChunkRecord] = []
    for index, chunk in enumerate(chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)):
        chunk_id = f"{path.stem}-text-{index}"
        metadata = {
            "source_file": path.name,
            "source_path": str(path),
            "source_type": "text",
        }
        records.append(ChunkRecord(chunk_id=chunk_id, text=chunk, metadata=metadata))
    return records


def load_file(path: Path, *, chunk_size: int, chunk_overlap: int) -> list[ChunkRecord]:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")
    if suffix in {".csv", ".xlsx", ".xls"}:
        return load_tabular_file(path)
    if suffix == ".pdf":
        return load_pdf_file(path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return load_text_file(path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)


def supported_files_in(directory: Path) -> list[Path]:
    files = [path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def dump_manifest(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
