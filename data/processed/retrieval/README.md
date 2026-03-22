# Retrieval Artifacts

## English

This directory stores generated retrieval-index artifacts that are built from
the tracked ESCO source layer and the current retrieval-model configuration.

Expected generated files:

- `faiss_hnsw.index`
- `faiss_hnsw_manifest.json`

These files are now tracked by Git for the active Qwen3 retrieval
configuration because rebuilding the FAISS cache is expensive enough to be
worth preserving.

Rebuild or refresh them with:

```bash
python -m backend.scripts.build_retrieval_index
```

If the tracked FAISS index is already current but the local SQLite retrieval
rows are missing or stale, the build command restores the SQLite rows without a
full corpus re-embedding pass.

## Русский

Этот каталог хранит сгенерированные артефакты retrieval-index, которые
строятся из отслеживаемого ESCO source layer и текущей конфигурации
retrieval-моделей.

Ожидаемые генерируемые файлы:

- `faiss_hnsw.index`
- `faiss_hnsw_manifest.json`

Эти файлы теперь отслеживаются Git для активной конфигурации retrieval на
Qwen3, потому что пересборка FAISS-кэша достаточно дорога и ее имеет смысл
сохранять.

Пересобрать или обновить их можно командой:

```bash
python -m backend.scripts.build_retrieval_index
```

Если отслеживаемый FAISS-index уже актуален, а локальные SQLite retrieval-rows
отсутствуют или устарели, команда сборки восстановит SQLite-rows без полного
повторного прохода эмбеддинга по корпусу.
