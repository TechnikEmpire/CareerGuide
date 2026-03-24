# Retrieval Artifacts

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
