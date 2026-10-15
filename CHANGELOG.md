# Changelog

## 1.1 — 2026-10-15

Data file unchanged (`mas_arkts_dataset.csv`, md5 8ac436943a8a357ef811275e96953aac).

- README rewritten: corrected statements (no deduplication was applied; the file holds no compiler
  diagnostics), documented the 60 repeated prompts and the repeated-code clusters, documented the
  `enhanced_prompt`/`enhancement_attempted` and `import_count` details, added the paper citation,
  license and contact.
- Added `DATASHEET.md` (datasheet for datasets).
- Added `REPRODUCIBILITY.md`: software versions, model configuration, iteration limits, compilation
  protocol, scoring prompt and human-validation protocol.
- Added `coverage/` with machine-readable coverage tables and `scripts/compute_coverage.py` that
  regenerates them, plus `scripts/verify_statistics.py` that recomputes the headline numbers.
- `dataset_schema.json`: version 1.1, notes on `quality_score` (all records vs compiled records),
  `enhanced_prompt`, `import_count`.
- License: data and documentation now under CC BY 4.0 (`LICENSE`); scripts under MIT (`LICENSE-CODE`).
  Version 1.0 was released under MIT and remains so in the repository history.
- `checksums.md5` regenerated for all files.

## 1.0 — 2025-09-15

Initial release: `mas_arkts_dataset.csv`, `dataset_schema.json`, `README.md`, `LICENSE`, `checksums.md5`.
