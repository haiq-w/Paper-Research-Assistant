#!/usr/bin/env python3
"""Search a paper index and return page-aware passages as JSON."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def fts_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[\w\-]+", query, flags=re.UNICODE)
    return [f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens if token]


def run_search(connection: sqlite3.Connection, match: str, limit: int):
    return connection.execute(
        """
        SELECT p.title, p.authors, p.year, p.path, c.page, c.chunk_no,
               c.text, bm25(chunks_fts) AS score
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.rowid
        JOIN papers p ON p.id = c.paper_id
        WHERE chunks_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (match, limit),
    ).fetchall()


def rerank(rows, limit: int):
    ranked = []
    for row in rows:
        item = dict(row)
        year_citations = len(re.findall(r"\b(?:19|20)\d{2}\b", item["text"]))
        reference_penalty = 6.0 if year_citations >= 5 else 0.0
        item["adjusted_score"] = item["score"] + reference_penalty
        ranked.append(item)
    ranked.sort(key=lambda item: item["adjusted_score"])
    return ranked[:limit]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()
    if not args.index.is_file():
        raise SystemExit(f"Index does not exist: {args.index}")
    tokens = fts_tokens(args.query)
    if not tokens:
        raise SystemExit("Query contains no searchable terms")

    connection = sqlite3.connect(args.index)
    connection.row_factory = sqlite3.Row
    limit = max(1, min(args.limit, 50))
    mode = "all"
    pool_size = max(50, limit * 10)
    rows = run_search(connection, " AND ".join(tokens), pool_size)
    if not rows:
        mode = "any"
        rows = run_search(connection, " OR ".join(tokens), pool_size)
    connection.close()
    results = rerank(rows, limit)
    result = {"query": args.query, "mode": mode, "count": len(results), "results": results}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
