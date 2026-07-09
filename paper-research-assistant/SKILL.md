---
name: paper-research-assistant
description: Search a configured local PDF paper library, retrieve evidence with file and page provenance, closely read and compare papers, check manuscript claims, and polish Chinese or English academic writing without changing scientific meaning. Use for literature search, paper reading, literature synthesis, citation verification, argument support, or academic manuscript polishing grounded in the user's local papers.
---

# Paper Research Assistant

Use the local library as an evidence source for paper reading and academic writing. Keep source statements, interpretation, and writing advice visibly separate.

## Library configuration

Use the library path supplied by the user. If the user has not supplied a path and no valid index exists, ask for the local PDF library directory before searching.

For a personal installation, the user may edit this section to add a private default path, for example `D:\paper_reading_skills`. Do not assume the repository author's local path.

The default index is `data/library.sqlite3` relative to this skill folder.

## Workflow

1. Identify whether the request is evidence search, close reading, comparison, synthesis, claim checking, or polishing.
2. Build the index when it is missing or when the library path changes:
   `python scripts/build_index.py --library "<library-path>" --index data/library.sqlite3`
3. Incrementally index newly added PDFs without reprocessing existing papers:
   `python scripts/build_index.py --library "<library-path>" --index data/library.sqlite3 --resume`
   Run a full build without `--resume` after files are moved, renamed, deleted, or replaced so stored paths remain accurate.
4. Search before making any library-specific claim:
   `python scripts/search_library.py --index data/library.sqlite3 --query "<query>" --limit 8`
5. Inspect retrieved passages. Increase `--limit` or use alternate technical terms when recall is weak.
6. Cite evidence as `[title, PDF p. N]` and include the source file path when the user needs traceability.
7. State `论文库中未找到充分证据` when the retrieved text does not support a claim.

Do not treat a filename, abstract snippet, or search score as proof. Base claims on inspected passage text.

## Evidence rules

Read `references/citation-policy.md` for evidence search, synthesis, comparison, and claim checking.

- Never invent titles, authors, years, DOI values, quotations, or page numbers.
- Distinguish a paper's explicit statement from an inference.
- Mention conflicting findings and scope limitations.
- Prefer several independent passages for broad conclusions.
- Treat PDF page numbers as physical PDF pages unless printed page numbering was independently verified.

## Close reading

Read `references/reading-protocol.md`. Use `assets/reading-note-template.md` when a structured note is requested. Cover the research problem, assumptions, method, identification or proof strategy, results, novelty, limitations, and connections to other indexed papers.

## Academic polishing

Read `references/polishing-rules.md`. Preserve equations, symbols, numbers, citation keys, causal strength, and technical meaning. Default to moderate academic editing. Return:

1. Revised text.
2. Material changes or ambiguities.
3. Claims that need evidence.
4. Relevant local-library evidence only when search was requested or would materially affect accuracy.

Do not add a scientific claim merely to make prose sound stronger.

## Script output

Both scripts emit UTF-8 JSON so results remain machine-readable. `build_index.py` deduplicates identical PDFs by SHA-256 without deleting source files. If extraction returns little or no text, report that OCR is required; do not silently index an unreadable scan.
