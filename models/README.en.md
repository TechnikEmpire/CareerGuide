# Local Model Cache

Last updated: 2026-03-22

This directory stores local runtime model artifacts that are required for
offline or mostly-offline development, but are not tracked in Git.

Expected contents after running the local setup script:

- `models/Qwen3-0.6B-GGUF/`
- `models/Qwen3-Embedding-0.6B/`

Optional contents for future ablations:

- `models/Qwen3-Reranker-0.6B/`

These files are intentionally ignored by Git because they are large, machine-
local runtime dependencies rather than authored project artifacts.

Use the canonical setup helper to populate this directory:

```bash
python -m backend.scripts.setup_local_models
```

That helper also updates:

- `.env.local`
- `config/llama_cpp_python_server.local.json`

The generated `.env.local` records both the stable logical model IDs and the
repo-local filesystem paths used at runtime.
