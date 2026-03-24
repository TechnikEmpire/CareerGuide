# Local Workflow

Last updated: 2026-03-23

### What This Workflow Is For

This document explains the current local development workflow in plain terms.

For the single-image deployment path, use [docs/DEPLOYMENT.en.md](DEPLOYMENT.en.md).

At this stage of the project, there are four different kinds of work:

1. one-time corpus preprocessing
2. one-time or infrequent retrieval-index building
3. repeatable local evaluation and answer-generation validation
4. repeatable web UI development against the stable backend contracts

These are different steps. They are not the same thing.

### What Has Already Been Done

The following heavyweight steps are already completed and tracked in Git:

- ESCO normalization
- English-to-Russian ESCO translation
- FAISS HNSW retrieval-index build
- dense-versus-reranker retrieval evaluation

That means the project is no longer in corpus-preparation mode.

### What The Project Is Doing Now

The active baseline is now:

1. use the tracked ESCO artifacts
2. use the tracked FAISS HNSW retrieval index
3. embed only the incoming query
4. retrieve dense ANN chunks
5. build a grounded prompt
6. ask the local Qwen3 GGUF generator for an answer
7. score the generated answer against tracked answer-eval cases

The active dense-only runtime default is now `top_k=10`, based on the current
tracked tuning curve.

### How Memory Works In The Current App

The local app is no longer using fake in-process-only memory.

At the current stage:

- user memory is persisted in the local SQLite `memory_items` table
- `/chat/answer` now extracts sentence-level memory candidates from the user question through the tracked binary BiLSTM bundle
- sentence segmentation prefers `pySBD` and falls back to a lightweight regex splitter if `pysbd` is not yet installed in the app environment
- the persisted memory set is read back immediately and summarized for prompt assembly
- duplicate memory text is collapsed by normalized text per user
- the trained standalone binary BiLSTM extractor under `tooling/memory_extraction/` is now wired into the live write path

This is still a narrow first slice, not the final memory system. The current
binary gate captures sentence-level memory candidates, but richer type
classification and lifecycle behavior are still not wired in.

The current runtime shape for the trained classifier is now:

1. normalize one incoming user turn
2. split it into sentence-like segments with `pySBD` when available and regex fallback otherwise
3. run the binary `MEMORY` vs `NO_MEMORY` classifier on each segment
4. convert positive segments into `MemoryItemPayload` records
5. dedupe them within the request and upsert them into `memory_items`
6. let Hopfield recall read the already deduplicated persistent store

The current memory read is no longer only a vague scaffold. It now performs a
basic non-trainable Hopfield recall over real embedding-space memory vectors:

- `top1` = sharp single-memory max-energy recall
- `topk` = exact top-k masking plus renormalization over softmax weights

This phase is based on Davydov, Jaffe, Singh, and Bullo, "Retrieving
k-Nearest Memories with Modern Hopfield Networks"; see
`docs/papers/33_Retrieving_k_Nearest_Memori.pdf` and
`docs/papers/hopfield_memory.txt`.

### Как память работает в текущем приложении

Локальное приложение больше не использует фальшивую память только внутри
процесса.

На текущем этапе:

- user memory сохраняется в локальной SQLite-таблице `memory_items`
- `/chat/answer` теперь извлекает sentence-level memory-candidates из вопроса пользователя через отслеживаемый binary BiLSTM bundle
- sentence-segmentation предпочитает `pySBD` и откатывается к легкому regex-splitter, если `pysbd` еще не установлен в app-env
- persisted memory сразу читается обратно и суммируется для prompt assembly
- дублирующийся memory-text схлопывается по normalized-text отдельно для каждого пользователя
- обученный standalone binary BiLSTM-extractor из `tooling/memory_extraction/` теперь уже подключен к live write-path

Это все еще узкий первый slice, а не финальная memory-system. Текущая
binary-gate ловит sentence-level memory-candidates, но более богатая
type-classification и lifecycle behavior пока еще не подключены.

Текущая runtime-схема работы обученного classifier теперь такая:

1. нормализовать один входной user turn
2. разбить его на sentence-like segments через `pySBD`, когда он доступен, и через regex-fallback в противном случае
3. прогнать binary-classifier `MEMORY` vs `NO_MEMORY` по каждому segment
4. превратить positive segments в записи `MemoryItemPayload`
5. дедуплицировать их внутри запроса и upsert-ить в `memory_items`
6. позволить Hopfield-recall читать уже дедуплицированный persistent store

Текущий memory-read больше не является только расплывчатым scaffold-ом. Он
теперь выполняет базовый нетренируемый Hopfield recall поверх memory-векторов
в реальном embedding-space:

- `top1` = резкий single-memory max-energy recall
- `topk` = exact top-k masking с перенормировкой softmax-весов

Этот этап опирается на работу Davydov, Jaffe, Singh и Bullo, "Retrieving
k-Nearest Memories with Modern Hopfield Networks"; см.
`docs/papers/33_Retrieving_k_Nearest_Memori.pdf` и
`docs/papers/hopfield_memory.txt`.

### Why Local Models Are Still Needed

Even though the retrieval index is already built, answer generation still needs:

- a local generator runtime for `Qwen/Qwen3-0.6B-GGUF:Q8_0`
- a local embedding model for query embedding (`Qwen/Qwen3-Embedding-0.6B`)

The retrieval index stores document vectors, but the system still needs to
embed each incoming query before it can search the index.

The repo-local setup helper writes `.env.local`, and the backend loads that file
automatically. That is how the local query-embedding model path is activated
without manual shell exports.

### What The Current Web UI Does

The first UI baseline now exists under `frontend/`.

At the current stage it supports:

- profile selection through a user-id field
- grounded chat through `POST /chat/answer`
- explicit citation display
- explicit “memory used” display from the answer response
- structured plan generation through `POST /career/plan`
- memory inspection through `GET /memory/list`

It is intentionally thin. The UI calls the FastAPI backend directly and does
not add a second AI-runtime layer on the frontend side.

### Canonical Local Commands

One-time local model setup:

```bash
python -m backend.scripts.setup_local_models
```

Start the full local app stack with one command:

```bash
python -m backend.scripts.run_local_app_stack --reload
```

This startup path now checks the retrieval artifacts before launching the
backend server and repairs them automatically when the tracked FAISS cache or
SQLite retrieval rows are stale.

When `--reload` is enabled, the backend now watches the `backend/` source tree
instead of mutable runtime artifacts like the local SQLite database, model
cache, or eval outputs. That avoids pointless backend restarts after normal app
requests mutate local state.

Когда включен `--reload`, backend теперь следит за деревом исходников
`backend/`, а не за изменяемыми runtime-артефактами вроде локальной SQLite-базы,
model-cache или eval-output. Это предотвращает бессмысленные перезапуски
backend после обычных app-запросов, которые меняют локальное состояние.

If you want to control the two processes manually, the advanced commands are:

```bash
python -m backend.scripts.run_local_generation_server
python -m backend.scripts.run_backend_dev_server --reload
```

Run the canonical local evaluation workflow:

```bash
python -m backend.scripts.run_local_eval_workflow
```

If the local generation server is already running, the evaluation wrapper will
reuse it instead of starting a duplicate process.
If the persisted retrieval artifacts are stale, the wrapper refreshes them
before it starts generation.

Run the frontend against the local backend:

```bash
cd frontend
npm install
npm run dev
```

The default frontend dev URL is `http://127.0.0.1:5173`. The backend now allows
local CORS requests from `127.0.0.1` and `localhost` on ports `5173` and
`3000`.

If the backend is not at `http://127.0.0.1:8000`, set `VITE_API_BASE_URL`
before launching the frontend.

### Canonical Hopfield Tests To Run

Targeted unit and smoke-level tests for the current Hopfield-memory slice:

```bash
python -m pytest backend/tests/test_hopfield_memory.py -q
python -m pytest backend/tests/test_memory_store.py -q
python -m pytest backend/tests/test_app.py -q
python -m pytest backend/tests/test_dev_server_scripts.py -q
```

These automated tests cover the Hopfield recall helpers, the app-level memory
path, and the reload-command construction without requiring multiple consoles.

Manual mode smoke for the live app:

```bash
CAREERGUIDE_MEMORY_HOPFIELD_MODE=top1 python -m backend.scripts.run_local_app_stack --reload
CAREERGUIDE_MEMORY_HOPFIELD_MODE=topk CAREERGUIDE_MEMORY_HOPFIELD_TOP_K=3 python -m backend.scripts.run_local_app_stack --reload
```

These manual runs should then be exercised with repeated `/chat/answer`
requests for the same user so you can inspect `/memory/list` and verify that
the prompt path reuses persisted memory under both recall modes.

### What The Evaluation Workflow Produces

The local evaluation workflow writes three canonical outputs:

- `eval/out/dense_retrieval_tuning.json`
- `eval/out/answer_predictions.json`
- `eval/out/answer_scores.json`

These answer three different questions:

- `dense_retrieval_tuning.json`
  - Which dense-only top-k choice currently scores best on the tracked qrels?
- `answer_predictions.json`
  - What answers and explicit cited chunk IDs did the current retrieval-plus-generation stack produce?
- `answer_scores.json`
  - How well do those generated answers overlap with the expected evidence chunks?

Answer-evidence scoring now depends on model-selected `cited_chunk_ids` rather
than on the full retrieved context list. Any older answer outputs produced
before that citation fix are obsolete and should be regenerated.
The next refresh should validate the new `top_k=10` default, the tighter
generation prompt/runtime settings, and the explicit citation path together.

### What We Are Not Doing

The current workflow is not:

- rebuilding the ESCO translation layer
- rebuilding the FAISS index on every run; it only refreshes retrieval artifacts when they are stale
- using the reranker in the active path
- shipping the final memory-comparison experiment yet

The reranker was already tested and kept only as a negative ablation record.
