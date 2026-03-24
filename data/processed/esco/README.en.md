# ESCO Processed Artifacts

This directory holds generated ESCO preprocessing artifacts.

Tracking policy:

- Raw vendor ESCO downloads under `data/raw/ESCO/` are ignored by git.
- Normalized concept and relation artifacts under `data/processed/esco/normalized/` are intended to be tracked.
- Bilingual translated concept output under `data/processed/esco/bilingual/` is intended to be tracked.
- Manifest files under `data/processed/esco/manifests/` are intended to be tracked.

Normalization policy:

- Concept records are keyed by ESCO `conceptUri`.
- If the vendor CSV contains duplicate concept rows with the same URI, preprocessing collapses them and keeps the latest `modifiedDate`.

This keeps the repo self-contained for continuation work while still avoiding
committing the raw vendor dump.
