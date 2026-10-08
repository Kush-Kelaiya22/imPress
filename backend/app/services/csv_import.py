"""Shared CSV reading for the bulk imports (#31 questions, #32 courses/sections).

Strict by design: the file must be UTF-8 (a BOM from Excel is fine), every
required column present, no unknown columns (an ignored "marks" column would
silently lose data), at most MAX_ROWS rows and MAX_BYTES bytes. Quoted
commas and line breaks are handled by the stdlib csv module. Errors that make
the whole file unusable raise CsvFileError (HTTP 422 with the reason);
per-row problems are reported by the caller.
"""

from __future__ import annotations

import csv
import io
import re

from fastapi import HTTPException, UploadFile

MAX_BYTES = 1_000_000
MAX_ROWS = 500


class CsvFileError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(422, detail)


async def read_upload(file: UploadFile, max_bytes: int = MAX_BYTES) -> bytes:
    """Read an uploaded file, refusing anything larger than max_bytes (413)."""
    raw = await file.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise HTTPException(413, f"File is larger than {max_bytes // 1000} KB")
    return raw


def _norm(header: str) -> str:
    return re.sub(r"[\s\-]+", "_", header.strip().lower())


def read_rows(raw: bytes, required: list[str], optional: list[str] = (),
              aliases: dict[str, str] | None = None, max_rows: int = MAX_ROWS) -> list[tuple[int, dict]]:
    """Parse CSV bytes into [(file line number, {column: stripped value})]."""
    if not raw.strip():
        raise CsvFileError("The file is empty")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise CsvFileError("The file is not UTF-8 text. In Excel use Save As → 'CSV UTF-8 (Comma delimited)'.")
    if "\x00" in text:
        raise CsvFileError("The file contains binary data; expected a CSV text file")

    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except (StopIteration, csv.Error) as e:
        raise CsvFileError(f"Could not read the header row: {e}")
    aliases = aliases or {}
    columns = [aliases.get(_norm(h), _norm(h)) for h in header]
    allowed = set(required) | set(optional)
    if dupes := sorted({c for c in columns if columns.count(c) > 1 and c}):
        raise CsvFileError(f"Duplicate column(s): {', '.join(dupes)}")
    if missing := [c for c in required if c not in columns]:
        raise CsvFileError(f"Missing required column(s): {', '.join(missing)}. "
                           f"Required: {', '.join(required)}")
    if unknown := [h for h, c in zip(header, columns) if c not in allowed]:
        raise CsvFileError(f"Unknown column(s): {', '.join(unknown)}. "
                           f"Allowed: {', '.join(list(required) + list(optional))}")

    rows: list[tuple[int, dict]] = []
    try:
        for cells in reader:
            line = reader.line_num
            if not any(c.strip() for c in cells):
                continue                                   # blank line
            if len(rows) >= max_rows:
                raise CsvFileError(f"Too many rows: the limit is {max_rows} per file")
            row = {c: (cells[i].strip() if i < len(cells) else "") for i, c in enumerate(columns)}
            if len(cells) > len(columns) and any(x.strip() for x in cells[len(columns):]):
                row["__extra__"] = f"{len(cells) - len(columns)} more cell(s) than columns"
            rows.append((line, row))
    except csv.Error as e:
        raise CsvFileError(f"Line {reader.line_num}: {e}")
    if not rows:
        raise CsvFileError("The file has a header but no data rows")
    return rows


_FORMULA = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value) -> str:
    """For CSV *exports*: stop spreadsheets evaluating user text as a formula."""
    s = "" if value is None else str(value)
    return "'" + s if s.startswith(_FORMULA) else s


def to_csv(header: list[str], rows: list[list]) -> str:
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\r\n")
    w.writerow(header)
    for r in rows:
        w.writerow([csv_safe(v) for v in r])
    return out.getvalue()


def text_key(s: str) -> str:
    """Duplicate detection key: case- and whitespace-insensitive."""
    return " ".join(s.casefold().split())
