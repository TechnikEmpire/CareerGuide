# ESCO Processed Artifacts

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
