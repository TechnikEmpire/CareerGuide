# Retrieval Artifacts

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
