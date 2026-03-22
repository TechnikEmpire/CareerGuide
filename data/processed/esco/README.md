# ESCO Processed Artifacts

## English

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

## Русский

Эта директория хранит сгенерированные ESCO preprocessing-артефакты.

Политика отслеживания:

- Raw vendor ESCO downloads в `data/raw/ESCO/` игнорируются git.
- Нормализованные артефакты concept и relation в `data/processed/esco/normalized/` предполагается отслеживать в git.
- Двуязычный translated concept output в `data/processed/esco/bilingual/` предполагается отслеживать в git.
- Manifest-файлы в `data/processed/esco/manifests/` предполагается отслеживать в git.

Политика нормализации:

- Concept records ключуются по ESCO `conceptUri`.
- Если vendor CSV содержит duplicate concept rows с одинаковым URI, preprocessing схлопывает их и сохраняет самую новую `modifiedDate`.

Это позволяет сделать репозиторий самодостаточным для продолжения работы,
не коммитя при этом raw vendor dump.
