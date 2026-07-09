#!/usr/bin/env python3
"""Build a page-aware SQLite FTS index from a local PDF library."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    from pypdf import PdfReader
except ImportError as exc:
    raise SystemExit("Missing dependency: pypdf. Run this script with the Codex bundled Python runtime.") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def chunks(text: str, size: int = 1800, overlap: int = 250):
    if not text:
        return
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            boundary = max(text.rfind(". ", start, end), text.rfind("\n", start, end))
            if boundary > start + size // 2:
                end = boundary + 1
        yield text[start:end].strip()
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)


def initialize(connection: sqlite3.Connection, reset: bool) -> None:
    if reset:
        connection.executescript(
            """
        DROP TABLE IF EXISTS chunks_fts;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS papers;
        """
        )
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY,
            sha256 TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            authors TEXT,
            year TEXT,
            path TEXT NOT NULL,
            page_count INTEGER NOT NULL,
            extracted_chars INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY,
            paper_id INTEGER NOT NULL REFERENCES papers(id),
            page INTEGER NOT NULL,
            chunk_no INTEGER NOT NULL,
            text TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            text,
            content='chunks',
            content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--resume", action="store_true", help="Continue a partial index instead of rebuilding it")
    args = parser.parse_args()

    library = args.library.expanduser().resolve()
    if not library.is_dir():
        raise SystemExit(f"Library directory does not exist: {library}")
    pdfs = sorted(
        library.rglob("*.pdf"),
        key=lambda path: (bool(re.search(r"\(\d+\)$", path.stem)), str(path).lower()),
    )
    args.index.parent.mkdir(parents=True, exist_ok=True)

    report = {"library": str(library), "found": len(pdfs), "indexed": 0, "already_indexed": 0, "duplicates": [], "unreadable": [], "errors": []}
    connection = sqlite3.connect(args.index)
    initialize(connection, reset=not args.resume)
    seen = {row[0]: row[1] for row in connection.execute("SELECT sha256, path FROM papers")}

    for file_number, path in enumerate(pdfs, start=1):
        try:
            fingerprint = sha256(path)
            if fingerprint in seen:
                if seen[fingerprint] == str(path):
                    report["already_indexed"] += 1
                else:
                    report["duplicates"].append({"path": str(path), "same_as": seen[fingerprint]})
                continue
            connection.execute("SAVEPOINT one_pdf")
            reader = PdfReader(str(path))
            metadata = reader.metadata or {}
            title = clean_text(str(metadata.get("/Title") or path.stem).strip())
            authors = clean_text(str(metadata.get("/Author") or "").strip())
            year_match = re.search(r"(?:19|20)\d{2}", str(metadata.get("/CreationDate") or path))
            year = year_match.group(0) if year_match else ""
            pages = []
            extracted_chars = 0
            for page_number, page in enumerate(reader.pages, start=1):
                text = clean_text(page.extract_text() or "")
                extracted_chars += len(text)
                pages.append((page_number, text))
            cursor = connection.execute(
                "INSERT INTO papers (sha256,title,authors,year,path,page_count,extracted_chars) VALUES (?,?,?,?,?,?,?)",
                (fingerprint, title, authors, year, str(path), len(reader.pages), extracted_chars),
            )
            paper_id = cursor.lastrowid
            for page_number, text in pages:
                for chunk_number, text_chunk in enumerate(chunks(text)):
                    if text_chunk:
                        connection.execute(
                            "INSERT INTO chunks (paper_id,page,chunk_no,text) VALUES (?,?,?,?)",
                            (paper_id, page_number, chunk_number, text_chunk),
                        )
            if extracted_chars < max(200, len(reader.pages) * 50):
                report["unreadable"].append({"path": str(path), "pages": len(reader.pages), "characters": extracted_chars})
            connection.execute("RELEASE one_pdf")
            connection.commit()
            seen[fingerprint] = str(path)
            report["indexed"] += 1
            if file_number % 10 == 0:
                print(f"Processed {file_number}/{len(pdfs)} files", file=sys.stderr, flush=True)
        except Exception as exc:  # keep indexing other papers
            try:
                connection.execute("ROLLBACK TO one_pdf")
                connection.execute("RELEASE one_pdf")
            except sqlite3.Error:
                connection.rollback()
            report["errors"].append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})

    connection.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    connection.commit()
    connection.close()
    report["index"] = str(args.index.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
