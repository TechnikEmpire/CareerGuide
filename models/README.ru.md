# Local Model Cache

Этот каталог хранит локальные model-артефакты runtime, которые нужны для
offline или почти-offline разработки, но не отслеживаются в Git.

Ожидаемое содержимое после запуска локального setup-скрипта:

- `models/Qwen_Qwen3.5-2B-GGUF/`
- `models/Qwen3-Embedding-0.6B/`

Опциональное содержимое для будущих ablation:

- `models/Qwen3-Reranker-0.6B/`

Эти файлы намеренно игнорируются Git, потому что они являются большими
локальными runtime-зависимостями, а не authored project-артефактами.

Используйте канонический setup-helper для заполнения этого каталога:

```bash
python -m backend.scripts.setup_local_models
```

Этот helper также обновляет:

- `.env.local`
- `config/llama_cpp_python_server.local.json`

Сгенерированный `.env.local` записывает и стабильные логические model ID, и
repo-local filesystem-path, которые используются во время runtime.
