from pathlib import Path

import pandas as pd

from app.ingestion import chunk_text, load_file


def test_chunk_text_respects_overlap() -> None:
    text = "A" * 400 + "\n\n" + "B" * 400 + "\n\n" + "C" * 400
    chunks = chunk_text(text, chunk_size=450, chunk_overlap=50)
    assert len(chunks) >= 3
    assert all(chunks)


def test_load_csv_creates_tabular_records(tmp_path: Path) -> None:
    sample = tmp_path / "errors.csv"
    pd.DataFrame(
        [
            {"error_code": "ERR-101", "error_message": "Login failed", "resolution": "Reset the password"},
            {"error_code": "ERR-102", "error_message": "Timeout", "resolution": "Retry later"},
        ]
    ).to_csv(sample, index=False)

    records = load_file(sample, chunk_size=500, chunk_overlap=50)
    assert len(records) == 2
    assert "Error code: ERR-101" in records[0].text
