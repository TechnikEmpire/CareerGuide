# Memory Extraction Tooling

## English

### Purpose

This directory contains standalone tooling for bilingual sentence-level memory
extraction.

Its role is intentionally narrow and explicit:

1. generate synthetic supervision data in Russian and English
2. prepare train/dev/test splits
3. train a lightweight BiLSTM classifier
4. evaluate the classifier
5. export a reusable inference bundle for later backend integration

This tooling is separate from the live backend on purpose.

- The **extractor classifier** decides whether a user sentence should become a
  persisted memory item and, if so, what type of memory it is.
- The **Hopfield memory layer** decides how already-stored memory vectors are
  recalled later during answering.

Those are different problems and should remain different modules.

This tooling does **not** yet replace the live heuristic extractor in
`backend/app/services/memory/memory_extract.py`. It is the training and
evaluation path for the next extraction baseline.

### Why This Exists

The current live extractor is only a simple heuristic. That is useful for early
wiring, but it is too weak for the intended Russian-first product behavior.

The BiLSTM baseline exists because it is:

- small enough to train and inspect easily
- aligned with the student's recurrent-network background
- easier to defend academically than a vague prompt-only extraction story
- separate from the heavier retrieval and generation runtime

This keeps the project honest:

- retrieval remains retrieval
- generation remains generation
- extraction becomes a real supervised classification task

### Label Schema

The current label space is intentionally fixed and small:

- `NO_MEMORY`
- `PREFERENCE`
- `CONSTRAINT`
- `GOAL`
- `AVAILABILITY`

What each label means:

- `NO_MEMORY`
  The sentence is career-adjacent or conversational, but does not express a
  stable memory worth persisting.
- `PREFERENCE`
  The sentence expresses a stable preference, such as preferring remote work or
  disliking frequent travel.
- `CONSTRAINT`
  The sentence expresses a hard limitation or non-negotiable condition.
- `GOAL`
  The sentence expresses a target role, transition direction, or future
  objective.
- `AVAILABILITY`
  The sentence expresses time, schedule, workload, budget, or energy limits.

Design rule:

- the raw synthetic corpus keeps the fine-grained labels
- the first trainable classifier baseline is binary: `MEMORY` vs `NO_MEMORY`
- fine-grained type classification remains useful later, but it is not the
  first supervised target anymore

### Binary-First Training Policy

The repository now uses a binary-first extraction strategy.

Why:

- the first runtime decision is whether a sentence should be stored as memory
  at all
- a binary task is easier to debug than a noisy five-way synthetic task
- this reduces the risk that the BiLSTM learns prompt-specific lexical cues
  instead of robust memory detection

Current intended flow:

1. generate raw synthetic records with the fine-grained labels
2. collapse those raw labels into `MEMORY` vs `NO_MEMORY` for the first BiLSTM
3. train and validate the binary classifier first
4. add type classification later after the binary baseline is credible

### How Synthetic Data Generation Works

This section is the most important one if you want to understand what the tool
is actually doing.

#### 1. Buckets are defined by `(language, label)`

The generator does **not** just ask the model for "a lot of examples".

It iterates over every bucket:

- `ru:NO_MEMORY`
- `ru:PREFERENCE`
- `ru:CONSTRAINT`
- `ru:GOAL`
- `ru:AVAILABILITY`
- `en:NO_MEMORY`
- `en:PREFERENCE`
- `en:CONSTRAINT`
- `en:GOAL`
- `en:AVAILABILITY`

For each bucket, it keeps generating until it reaches the target count, such as
`100` or `1000` examples.

#### 2. The generator uses a direct local model, not the app server

Synthetic corpus generation is a standalone GPU workflow.

It loads a local or Hugging Face causal-language model directly inside the
tooling process via `transformers`. It does **not** go through the app's
OpenAI-compatible runtime server.

That is deliberate:

- you keep explicit control over the local generation model
- you can choose model source, dtype, device, and seed directly
- you avoid app-server overhead and indirection

Current default model family:

- `Qwen/Qwen3-0.6B`

Important constraint:

- this tooling needs a **transformers-compatible model directory or repo id**
- a `.gguf` file is **not** valid here
- `.gguf` belongs to the app's `llama.cpp` runtime path, not to this training tool

#### 3. The model is prompted per bucket

The prompt template lives in:

- `tooling/memory_extraction/prompts.py`

The prompt tells the model:

- which language to use
- which label to target
- that each completion should contain exactly one example sentence
- that examples should be natural user utterances rather than generic advice
- what counts as a valid instance for that label

Current format contract:

- one example sentence per line
- no numbering
- no bullets
- no quotes
- no markdown
- no extra commentary

This format is intentionally simpler and more robust than requiring perfect
JSON from every generation call.

Important prompt-design note:

- the generator is not trying to create narrow ESCO facts
- it is trying to create user utterances that reveal stable memory signals
- the prompt now aims for a mix of first-person statements, short fragments,
  indirect phrasing, and mildly messy chat wording
- the prompt rotates example subsets and topic hints across attempts instead of
  staying frozen on one few-shot block
- when a bucket starts collapsing onto repeated openings, later prompts
  explicitly tell the model which openings to avoid
- the prompt explicitly rejects generic advice such as "It is important to..."
  or "Важно..."
- this matters because vague advice sentences otherwise leak into multiple label
  buckets, especially `PREFERENCE` and `NO_MEMORY`

#### 3a. Why generation is faster now

The generator no longer asks the model for one long completion that contains
many examples.

That old pattern was slow for two reasons:

- generation stayed mostly sequential and under-used the GPU
- long outputs increased formatting drift and parser failures

The current generator instead does this:

1. build one prompt for one target bucket
2. ask for exactly one sentence per completion
3. sample many completions in parallel in a single `generate(...)` call

That means:

- `batch_size` now means **parallel sampled completions per call**
- `max_tokens` now means **maximum new tokens for one sentence**
- the GPU gets a more meaningful batch dimension
- each completion is shorter, so throughput is much better
- parsing is simpler because each sample is supposed to be a single utterance

#### 4. The parser accepts multiple output styles

The parser in:

- `tooling/memory_extraction/generate_synthetic_dataset.py`

tries to recover examples from model output in this order:

1. structured JSON with an `examples` list
2. loose JSON-object streams such as repeated
   `{"sentence": "...", "label": "NO_MEMORY"}`
3. plain one-sentence-per-line output

This matters because small local models often drift in formatting even when the
semantic content is fine.

The generator therefore tries to recover useful training sentences instead of
throwing everything away just because the formatting is imperfect.

What the parser does **not** do yet:

- it does not run a second semantic verifier before accepting a sentence
- so corpus quality still depends heavily on prompt quality plus human spot
  checks

#### 5. Quality control happens after generation

The generator does script-side validation:

- language check
  - `ru` requires Cyrillic
  - `en` requires Latin and rejects Cyrillic
- lightweight semantic gate
  - rejects obvious chain-of-thought and prompt leakage
  - rejects lines that do not look like one plausible user sentence
  - rejects a small set of known small-model artifact phrasings and incomplete
    clause fragments
  - does **not** enforce the target class through keyword lists
- empty-line filtering
- exact duplicate filtering through normalized text keys
- near-duplicate filtering through token-set overlap against already accepted
  examples
- repeated-opening filtering so one bucket does not fill with the same
  `I prefer...` or `Я не уверен...` stem

This is still intentionally lightweight.

It is **not** a full language-ID model, semantic deduper, or external
verification model.
It is just enough to prevent obviously bad synthetic data from flooding the
corpus when a small local generator starts producing prompt-following chatter.

The generator also prints bucket diagnostics for rejected examples so that you
can see whether a bucket is failing mainly because of:

- language mismatch
- semantic rejection
- duplicate collapse
- near-duplicate collapse
- repeated opening collapse
- generation errors

The generator also stops a bucket after too many **consecutive** no-progress
attempts instead of only relying on one blunt total-attempt cap.
That matters because small local models sometimes keep producing the same few
templates forever once a bucket collapses.

#### 6. Data is checkpointed incrementally

Accepted examples are appended to disk as they are generated.

That means:

- one bad generation call does not lose all previous progress
- interrupted runs can be resumed more safely
- the tool is usable for long GPU runs

### What Is Written to Disk

Each accepted sentence becomes a `MemoryExtractionRecord` with fields like:

- `record_id`
- `language`
- `label`
- `text`
- `source`
- `source_model`
- `prompt_name`

The schema lives in:

- `tooling/memory_extraction/schema.py`

The raw generated dataset is written to:

- `tooling/memory_extraction/data/synthetic_memory_sentences.jsonl`

### How Dataset Preparation Works

The preparation step is implemented in:

- `tooling/memory_extraction/prepare_dataset.py`

This step:

1. reads the full synthetic corpus
2. optionally projects the raw fine-grained labels into the chosen classifier task
3. groups records by `(language, label)`
4. shuffles each bucket deterministically with a fixed seed
5. splits each bucket into train/dev/test
6. writes the split files and a split manifest

Why this matters:

- it prevents one label-language bucket from disappearing from a split
- it keeps evaluation more stable and interpretable
- it avoids accidental train/test skew when the corpus is imbalanced
- it lets the repo keep fine-grained raw labels while training the first model
  on the simpler binary task

The split outputs are:

- `tooling/memory_extraction/data/splits/train.jsonl`
- `tooling/memory_extraction/data/splits/dev.jsonl`
- `tooling/memory_extraction/data/splits/test.jsonl`
- `tooling/memory_extraction/data/split_manifest.json`

### How the BiLSTM Training Works

The training logic is in:

- `tooling/memory_extraction/train_bilstm_classifier.py`
- `tooling/memory_extraction/classifier.py`

#### 1. Tokenization

This baseline uses a simple regex tokenizer, not a BPE tokenizer.

The tokenizer:

- lowercases text
- splits words and punctuation with a Unicode-aware regex

That is intentionally simple and inspectable.

#### 2. Vocabulary

The vocabulary is built **only from the training split**.

Special tokens:

- `<pad>`
- `<unk>`

Any unseen token at inference time becomes `<unk>`.

This is standard for lightweight supervised baselines and avoids leakage from
dev/test into the training vocabulary.

#### 3. Model architecture

The classifier is:

- embedding layer
- bidirectional LSTM
- concatenation of the final forward and backward hidden states
- dropout
- linear classification head

So the model computes:

1. token embeddings
2. contextual sequence encoding with a BiLSTM
3. one sentence representation from the final hidden states
4. logits over the labels used by the chosen task

This is intentionally a classic supervised sequence classifier.

#### 4. Objective and optimization

Training uses:

- cross-entropy loss
- Adam optimizer

At the end of each epoch, the model is evaluated on the dev split.

The checkpoint selection rule is:

- keep the model state with the best dev `macro_f1`

That matters because the binary task is still imbalanced in practice, and later
multiclass runs will be even more so. `macro_f1` is therefore a better main
selection metric than raw accuracy alone.

### How Evaluation Works

Evaluation is implemented in:

- `tooling/memory_extraction/evaluate_classifier.py`
- `tooling/memory_extraction/metrics.py`

The evaluation report includes:

- accuracy
- macro-F1
- per-label precision/recall/F1
- confusion-style counts
- per-language metrics for `ru` and `en`

That means you can inspect:

- overall classifier quality
- whether one label is collapsing into another
- whether Russian and English behavior are balanced or skewed

### Model Artifact Format

The trained model is saved as a PyTorch bundle:

- `model_state_dict`
- `token_to_id`
- `label_to_id`
- model config

Current output file:

- `tooling/memory_extraction/models/bilstm_memory_classifier.pt`

Why this format:

- easiest first integration path
- smallest engineering delta for the backend
- easy to inspect and reload

This is **not** a `llama.cpp` model and should not be confused with the GGUF
generator runtime.

### Recommended Workflow

#### 1. Install the standalone tooling environment

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/memory_extraction/requirements.txt
```

#### 2. Generate a small validation corpus first

Do **not** start with the full 10k corpus if you have not validated generation
quality yet.

Start with:

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset \
  --model-source /mnt/e/Work-Repos-SiftVPN/CareerGuide/models/Qwen3-0.6B-Transformers \
  --local-files-only \
  --device cuda \
  --dtype float16 \
  --seed 17 \
  --batch-size 32 \
  --max-tokens 64 \
  --examples-per-label 100
```

#### 3. Scale up once the output looks healthy

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset \
  --model-source /mnt/e/Work-Repos-SiftVPN/CareerGuide/models/Qwen3-0.6B-Transformers \
  --local-files-only \
  --device cuda \
  --dtype float16 \
  --seed 17 \
  --batch-size 48 \
  --max-tokens 64 \
  --examples-per-label 250 \
  --append
```

#### 3a. Throughput tuning

If the GPU is underutilized, increase `--batch-size` first.

Recommended order of tuning:

1. keep `--dtype float16`
2. keep `--max-tokens` small, usually `48` to `96`
3. increase `--batch-size` until you see healthy GPU utilization or memory
   pressure
4. only then consider scaling `--examples-per-label`

Practical guidance for a 4090-class workstation:

- start around `--batch-size 32`
- try `--batch-size 48` or `64` if memory allows
- avoid very large `--max-tokens` values like `512` for this task, because the
  task is single-sentence generation, not paragraph generation

Quality rule:

- improve sample quality first
- then scale dataset size

For this baseline, a clean `250` to `500` examples per bucket is often more
useful than a noisy `1000`.

#### 4. Prepare splits

```bash
python -m tooling.memory_extraction.prepare_dataset --task binary
```

#### 5. Train the BiLSTM

```bash
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
```

#### 6. Evaluate the classifier

```bash
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

### Expected Outputs

Generated data:

- `tooling/memory_extraction/data/synthetic_memory_sentences.jsonl`
- `tooling/memory_extraction/data/splits/binary/train.jsonl`
- `tooling/memory_extraction/data/splits/binary/dev.jsonl`
- `tooling/memory_extraction/data/splits/binary/test.jsonl`
- `tooling/memory_extraction/data/split_manifest_binary.json`

Model artifacts:

- `tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`
- `tooling/memory_extraction/models/bilstm_memory_classifier_binary_train_report.json`
- `tooling/memory_extraction/models/bilstm_memory_classifier_binary_eval_report.json`

These artifacts may be committed to the repo when you want reproducible
supervision data, trained-model checkpoints, and evaluation outputs preserved
in version control.

### Current Validated Baseline State

The current tracked extraction baseline is no longer only a tooling scaffold.

Current tracked artifacts include:

- a complete `memory_extraction_synthetic_v4` ru/en corpus with `250` examples
  for each raw `(language, label)` bucket
- binary train/dev/test splits under `tooling/memory_extraction/data/splits/binary/`
- trained binary BiLSTM bundles and reports under
  `tooling/memory_extraction/models/`

Current interpretation:

- the standalone binary baseline is trained and evaluated
- the live backend still does **not** use it yet
- the next runtime step is sentence-level integration, not more synthetic-only
  plumbing

### Planned Backend Integration Shape

When this classifier is integrated into the live backend, the intended runtime
flow is:

1. normalize one user turn
2. split it into deterministic sentence-like segments
3. classify each segment independently as `MEMORY` or `NO_MEMORY`
4. convert positive segments into `MemoryItemPayload` items
5. dedupe them within the request and then upsert them into `memory_items`
6. let the existing Hopfield read operate over that deduplicated persistent
   store

This keeps extraction, persistence, deduplication, and Hopfield recall as
separate inspectable steps.

### Important Limitations

- v1 targets only `ru` and `en`
- quality control is still heuristic, not a full language-ID or semantic
  deduplication system
- synthetic generation quality depends strongly on the chosen local model and
  prompt discipline
- the live backend still uses heuristic memory extraction until this classifier
  is trained, validated, and integrated
- `importance` remains policy metadata; it is not a direct classifier output

## Русский

### Назначение

Этот каталог содержит standalone tooling для двуязычного sentence-level memory
extraction.

Его роль намеренно узкая и явная:

1. генерировать synthetic supervision-data на русском и английском
2. готовить train/dev/test splits
3. обучать легкий BiLSTM-classifier
4. оценивать classifier
5. экспортировать переиспользуемый inference-bundle для последующей
   интеграции в backend

Это tooling намеренно отделено от live-backend.

- **Extractor-classifier** решает, должна ли пользовательская фраза стать
  persisted memory item и какого она типа.
- **Hopfield memory layer** решает, как уже сохраненные memory-векторы потом
  извлекаются во время answering.

Это разные задачи и они должны оставаться разными модулями.

Пока это tooling **не** заменяет live heuristic extractor в
`backend/app/services/memory/memory_extract.py`. Это training- и
evaluation-path для следующего extraction-baseline.

### Зачем это нужно

Текущий live extractor — это только простая heuristic.

Она полезна для раннего wiring, но слишком слаба для целевого Russian-first
поведения продукта.

BiLSTM-baseline нужен потому что он:

- достаточно мал, чтобы его было легко обучать и inspect
- согласован с бэкграундом студентки в recurrent networks
- легче академически защищать, чем расплывчатую prompt-only extraction story
- отделен от более тяжелых retrieval и generation runtime

Это сохраняет проект честным:

- retrieval остается retrieval
- generation остается generation
- extraction становится реальной supervised classification-task

### Схема меток

Текущее label-space намеренно фиксировано и невелико:

- `NO_MEMORY`
- `PREFERENCE`
- `CONSTRAINT`
- `GOAL`
- `AVAILABILITY`

Что означает каждая метка:

- `NO_MEMORY`
  Фраза связана с карьерной темой или диалогом, но не выражает стабильную
  память, которую стоит сохранять.
- `PREFERENCE`
  Фраза выражает стабильное предпочтение, например любовь к remote-work или
  нежелание часто ездить в командировки.
- `CONSTRAINT`
  Фраза выражает жесткое ограничение или не-negotiable condition.
- `GOAL`
  Фраза выражает целевую роль, направление перехода или будущую цель.
- `AVAILABILITY`
  Фраза выражает ограничения по времени, графику, нагрузке, бюджету или
  энергии.

Правило дизайна:

- raw synthetic corpus сохраняет fine-grained labels
- первый обучаемый classifier baseline является бинарным: `MEMORY` vs `NO_MEMORY`
- fine-grained type classification остается полезной позже, но не является
  первой supervised-целью

### Политика binary-first обучения

Репозиторий теперь использует binary-first стратегию для extraction.

Почему:

- первое runtime-решение состоит просто в том, нужно ли вообще сохранять
  фразу как memory
- бинарную задачу легче отлаживать, чем шумную synthetic five-way задачу
- это снижает риск того, что BiLSTM выучит prompt-specific lexical cues вместо
  более устойчивого memory detection

Текущий intended flow:

1. сгенерировать raw synthetic records с fine-grained labels
2. схлопнуть эти raw labels в `MEMORY` vs `NO_MEMORY` для первого BiLSTM
3. сначала обучить и провалидировать binary classifier
4. добавлять type classification позже, когда binary baseline уже убедителен

### Как работает генерация synthetic data

Этот раздел самый важный, если нужно понять, что именно делает tooling.

#### 1. Генерация идет по bucket-ам `(language, label)`

Generator **не** просто просит модель выдать "много примеров".

Он проходит по каждому bucket:

- `ru:NO_MEMORY`
- `ru:PREFERENCE`
- `ru:CONSTRAINT`
- `ru:GOAL`
- `ru:AVAILABILITY`
- `en:NO_MEMORY`
- `en:PREFERENCE`
- `en:CONSTRAINT`
- `en:GOAL`
- `en:AVAILABILITY`

Для каждого bucket-а генерация повторяется, пока не будет достигнуто целевое
число примеров, например `100` или `1000`.

#### 2. Generator использует direct local model, а не app-server

Генерация synthetic corpus — это standalone GPU workflow.

Generator загружает локальную или Hugging Face causal-language model напрямую
внутрь tooling-процесса через `transformers`. Он **не** идет через
OpenAI-compatible runtime-server приложения.

Это сделано намеренно:

- вы сохраняете явный контроль над локальной generation-model
- можно напрямую выбирать source модели, dtype, device и seed
- отсутствует overhead и лишняя косвенность app-server

Текущее семейство моделей по умолчанию:

- `Qwen/Qwen3-0.6B`

Важное ограничение:

- этому tooling нужен **transformers-compatible model directory или repo id**
- `.gguf`-файл здесь **не** подходит
- `.gguf` относится к `llama.cpp` runtime-path приложения, а не к этому
  training-tool

#### 3. Модель промптится отдельно для каждого bucket

Шаблон prompt находится в:

- `tooling/memory_extraction/prompts.py`

Prompt сообщает модели:

- какой язык нужно использовать
- какой label целевой
- что каждый completion должен содержать ровно одно example sentence
- что примеры должны выглядеть как естественные user utterances, а не как generic advice
- что считается корректным instance для данного label

Текущий контракт формата:

- одно example sentence на строку
- без нумерации
- без bullets
- без кавычек
- без markdown
- без лишних комментариев

Этот формат намеренно проще и надежнее, чем требовать идеальный JSON от
каждого generation-call.

Важное замечание по prompt-дизайну:

- generator не пытается создавать узкие ESCO-факты
- он пытается создавать user utterances, которые раскрывают стабильные
  memory-signals
- prompt теперь пытается давать смесь first-person фраз, коротких fragments,
  непрямых формулировок и слегка небрежного chat-style wording
- prompt теперь ротирует subsets примеров и topic hints между попытками, а не
  остается одним и тем же few-shot блоком
- когда bucket начинает коллапсировать в одинаковые openings, следующие prompts
  явно запрещают слишком похожие начала фраз
- prompt явно запрещает generic advice вроде "It is important to..." или
  "Важно..."
- это важно, потому что расплывчатые advice-sentences иначе начинают
  протекать сразу в несколько label-buckets, особенно в `PREFERENCE` и
  `NO_MEMORY`

#### 3a. Почему генерация теперь быстрее

Generator больше не просит модель выдать один длинный completion, внутри
которого находится много примеров.

Старая схема была медленной по двум причинам:

- генерация оставалась в основном последовательной и плохо нагружала GPU
- длинные outputs сильнее провоцировали format drift и parser failures

Текущая схема делает следующее:

1. строит один prompt для одного target bucket
2. просит ровно одно предложение на completion
3. сэмплирует много completions параллельно в одном `generate(...)` call

Это означает:

- `batch_size` теперь означает **число параллельных sampled completions за вызов**
- `max_tokens` теперь означает **максимум новых токенов на одно предложение**
- GPU получает более полезное batch-измерение
- каждый completion становится короче, поэтому throughput заметно выше
- parsing проще, потому что каждый sample должен быть одной user utterance

#### 4. Parser принимает несколько стилей вывода

Parser в:

- `tooling/memory_extraction/generate_synthetic_dataset.py`

пытается восстановить примеры из model output в таком порядке:

1. структурный JSON с `examples`
2. loose JSON-object stream вида
   `{"sentence": "...", "label": "NO_MEMORY"}`
3. plain one-sentence-per-line output

Это важно, потому что маленькие локальные модели часто дрейфуют по формату,
даже если семантический контент в целом правильный.

Поэтому generator старается восстановить полезные training-sentences, а не
выбрасывать все только из-за imperfect formatting.

Что parser и quality gate пока **не** делают:

- они не используют отдельную verification-model
- они не гарантируют идеальную семантическую чистоту
- поэтому качество corpus все еще требует human spot-check проверки

#### 5. После генерации выполняется quality control

Generator делает script-side validation:

- language-check
  - для `ru` требуется кириллица
  - для `en` требуется латиница и запрещается кириллица
- lightweight semantic gate
  - отбрасывает очевидный chain-of-thought и prompt leakage
  - отбрасывает строки, которые не похожи на одно правдоподобное user sentence
  - отбрасывает небольшой набор известных small-model artifact phrasings и
    неполных clause-fragments
  - **не** навязывает целевой class через keyword-lists
- фильтрация пустых строк
- фильтрация exact duplicates через normalized text keys
- фильтрация near-duplicates по token-set overlap с уже принятыми примерами
- фильтрация повторяющихся sentence-openings, чтобы bucket не заполнялся одним
  и тем же stem вроде `Я предпочитаю...` или `Я не уверен...`

Это все еще намеренно lightweight-слой.

Это **не** полноценная language-ID model, не semantic deduper и не отдельная
verification-model.
Это минимальный барьер, чтобы synthetic corpus не заполнился очевидно плохими
примерами, когда небольшая локальная model начинает уходить в prompt-following
chatter.

Generator также печатает bucket diagnostics для rejected examples, чтобы было
видно, из-за чего bucket в основном проседает:

- language mismatch
- semantic rejection
- duplicate collapse
- near-duplicate collapse
- repeated opening collapse
- generation errors

Кроме того, generator теперь останавливает bucket после слишком большого числа
**последовательных** no-progress attempts, а не только по одному грубому
total-attempt cap.
Это важно, потому что маленькие локальные модели иногда после коллапса bucket
могут бесконечно крутиться вокруг нескольких одинаковых templates.

#### 6. Данные checkpoint-ятся инкрементально

Принятые примеры дописываются на диск по мере генерации.

Это означает:

- один неудачный generation-call не уничтожает весь предыдущий прогресс
- прерванные long GPU-runs можно безопаснее продолжать
- tooling становится практичным для долгих запусков

### Что записывается на диск

Каждое принятое предложение становится `MemoryExtractionRecord` с полями:

- `record_id`
- `language`
- `label`
- `text`
- `source`
- `source_model`
- `prompt_name`

Схема описана в:

- `tooling/memory_extraction/schema.py`

Raw generated dataset записывается в:

- `tooling/memory_extraction/data/synthetic_memory_sentences.jsonl`

### Как работает подготовка dataset

Этап preparation реализован в:

- `tooling/memory_extraction/prepare_dataset.py`

Этот этап:

1. читает полный synthetic corpus
2. при необходимости проецирует raw fine-grained labels в выбранную задачу classifier-а
3. группирует записи по `(language, label)`
4. детерминированно перемешивает каждый bucket с фиксированным seed
5. делит каждый bucket на train/dev/test
6. записывает split-файлы и split manifest

Почему это важно:

- это не дает какому-то label-language bucket исчезнуть из split-а
- это делает evaluation стабильнее и понятнее
- это защищает от случайного train/test skew при неравномерном corpus
- это позволяет хранить fine-grained raw labels, но обучать первый model на
  более простой binary-task

Split outputs:

- `tooling/memory_extraction/data/splits/binary/train.jsonl`
- `tooling/memory_extraction/data/splits/binary/dev.jsonl`
- `tooling/memory_extraction/data/splits/binary/test.jsonl`
- `tooling/memory_extraction/data/split_manifest_binary.json`

### Как работает обучение BiLSTM

Training-логика находится в:

- `tooling/memory_extraction/train_bilstm_classifier.py`
- `tooling/memory_extraction/classifier.py`

#### 1. Tokenization

Этот baseline использует простой regex-tokenizer, а не BPE-tokenizer.

Tokenizer:

- приводит текст к нижнему регистру
- делит слова и punctuation через Unicode-aware regex

Это намеренно простое и inspectable решение.

#### 2. Vocabulary

Vocabulary строится **только по training split**.

Специальные токены:

- `<pad>`
- `<unk>`

Любой unseen token на inference-time становится `<unk>`.

Это стандартно для lightweight supervised baselines и предотвращает leakage из
dev/test в training vocabulary.

#### 3. Архитектура модели

Classifier состоит из:

- embedding-layer
- bidirectional LSTM
- конкатенации последнего forward и backward hidden state
- dropout
- linear classification head

То есть модель вычисляет:

1. token embeddings
2. contextual sequence encoding через BiLSTM
3. одно sentence representation из final hidden states
4. logits по меткам выбранной classifier-task

Это намеренно классический supervised sequence-classifier.

#### 4. Objective и optimization

Training использует:

- cross-entropy loss
- Adam optimizer

В конце каждой эпохи модель оценивается на dev split.

Правило выбора checkpoint:

- сохраняется состояние модели с лучшим dev `macro_f1`

Это важно, потому что даже binary-task на практике несбалансирована, а более
поздние multiclass-runs будут еще более чувствительны к этому. Поэтому
`macro_f1` лучше подходит как главный selection-metric, чем чистая accuracy.

### Как работает evaluation

Evaluation реализована в:

- `tooling/memory_extraction/evaluate_classifier.py`
- `tooling/memory_extraction/metrics.py`

Evaluation report включает:

- accuracy
- macro-F1
- per-label precision/recall/F1
- confusion-style counts
- per-language metrics для `ru` и `en`

Это значит, что можно inspect:

- общее качество classifier
- не схлопывается ли один label в другой
- сбалансировано ли поведение между русским и английским

### Формат model artifact

Обученная модель сохраняется как PyTorch bundle:

- `model_state_dict`
- `token_to_id`
- `label_to_id`
- model config

Текущий output-file:

- `tooling/memory_extraction/models/bilstm_memory_classifier.pt`

Почему выбран именно такой формат:

- это самый простой первый integration-path
- минимальный engineering delta для backend
- bundle легко inspect и reload

Это **не** `llama.cpp` model и ее нельзя путать с GGUF generator runtime.

### Рекомендуемый workflow

#### 1. Установить standalone tooling environment

```bash
cd /mnt/e/Work-Repos-SiftVPN/CareerGuide
source ~/miniconda3/etc/profile.d/conda.sh

conda create -n careerguide-tools python=3.11 -y
conda activate careerguide-tools

python -m pip install --upgrade pip
python -m pip install -r tooling/memory_extraction/requirements.txt
```

#### 2. Сначала сгенерировать небольшой validation corpus

**Не** начинайте сразу с полного 10k corpus, если качество генерации еще не
проверено.

Сначала используйте:

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset \
  --model-source /mnt/e/Work-Repos-SiftVPN/CareerGuide/models/Qwen3-0.6B-Transformers \
  --local-files-only \
  --device cuda \
  --dtype float16 \
  --seed 17 \
  --batch-size 32 \
  --max-tokens 64 \
  --examples-per-label 100
```

#### 3. Масштабировать только после того, как output выглядит здоровым

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset \
  --model-source /mnt/e/Work-Repos-SiftVPN/CareerGuide/models/Qwen3-0.6B-Transformers \
  --local-files-only \
  --device cuda \
  --dtype float16 \
  --seed 17 \
  --batch-size 48 \
  --max-tokens 64 \
  --examples-per-label 250 \
  --append
```

#### 3a. Тюнинг throughput

Если GPU недогружен, сначала увеличивайте `--batch-size`.

Рекомендуемый порядок настройки:

1. оставить `--dtype float16`
2. держать `--max-tokens` маленьким, обычно в диапазоне `48`–`96`
3. увеличивать `--batch-size`, пока не появится нормальная загрузка GPU или
   не начнется давление по памяти
4. только после этого масштабировать `--examples-per-label`

Практический ориентир для workstation уровня 4090:

- начинать около `--batch-size 32`
- пробовать `--batch-size 48` или `64`, если хватает памяти
- избегать слишком больших `--max-tokens` вроде `512`, потому что здесь задача
  — генерация одного предложения, а не абзацев

Правило качества:

- сначала улучшайте качество sample-ов
- потом масштабируйте размер dataset

Для этого baseline чистые `250`–`500` примеров на bucket часто полезнее, чем
шумные `1000`.

#### 4. Подготовить splits

```bash
python -m tooling.memory_extraction.prepare_dataset --task binary
```

#### 5. Обучить BiLSTM

```bash
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
```

#### 6. Оценить classifier

```bash
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

### Ожидаемые outputs

Generated data:

- `tooling/memory_extraction/data/synthetic_memory_sentences.jsonl`
- `tooling/memory_extraction/data/splits/binary/train.jsonl`
- `tooling/memory_extraction/data/splits/binary/dev.jsonl`
- `tooling/memory_extraction/data/splits/binary/test.jsonl`
- `tooling/memory_extraction/data/split_manifest_binary.json`

Model artifacts:

- `tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`
- `tooling/memory_extraction/models/bilstm_memory_classifier_binary_train_report.json`
- `tooling/memory_extraction/models/bilstm_memory_classifier_binary_eval_report.json`

Эти артефакты могут коммититься в репозиторий, если вам нужно сохранять
воспроизводимые supervision-data, trained-model checkpoints и evaluation
outputs в version control.

### Текущее подтвержденное состояние baseline

Текущий extraction-baseline больше не является только tooling-scaffold.

В текущих отслеживаемых артефактах уже есть:

- полный ru/en-corpus `memory_extraction_synthetic_v4` с `250` примерами в
  каждом raw bucket `(language, label)`
- binary train/dev/test splits в
  `tooling/memory_extraction/data/splits/binary/`
- обученные binary BiLSTM bundles и reports в
  `tooling/memory_extraction/models/`

Текущая интерпретация:

- standalone binary baseline уже обучен и оценен
- live-backend его пока **не** использует
- следующий runtime-шаг — это sentence-level integration, а не еще один слой
  synthetic-only plumbing

### Планируемая схема backend-интеграции

Когда этот classifier будет интегрирован в live-backend, предполагаемый
runtime-flow такой:

1. нормализовать один user turn
2. разбить его на детерминированные sentence-like segments
3. независимо классифицировать каждый segment как `MEMORY` или `NO_MEMORY`
4. превратить positive segments в элементы `MemoryItemPayload`
5. дедуплицировать их внутри запроса и затем upsert-ить в `memory_items`
6. позволить существующему Hopfield-read работать уже поверх этого
   дедуплицированного persistent store

Так extraction, persistence, deduplication и Hopfield recall остаются
отдельными inspectable этапами.

### Важные ограничения

- v1 нацелен только на `ru` и `en`
- quality control все еще heuristic, а не полноценная language-ID или semantic
  deduplication система
- качество synthetic generation сильно зависит от выбранной локальной модели и
  дисциплины prompt-а
- live-backend все еще использует heuristic memory extraction, пока этот
  classifier не будет обучен, валидирован и интегрирован
- `importance` остается policy metadata; это не прямой output classifier
