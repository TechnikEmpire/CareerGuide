# Memory Extraction Tooling

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

This tooling is still the training and evaluation path for the extraction
baseline, but the tracked binary bundle now also feeds the live runtime path in
`backend/app/services/memory/memory_extract.py`.

### Why This Exists

The live runtime now already uses the tracked binary BiLSTM bundle for
sentence-level extraction. This tooling still matters because the student needs
a clear and reproducible path to improve that model instead of treating the
current bundle as fixed forever.

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
- the live backend now uses the tracked binary bundle in its sentence-level
  memory write path
- runtime sentence splitting now prefers `pySBD` and falls back to regex if
  `pysbd` is not yet installed in the app environment
- the next runtime step is real-chat evaluation and debugging, not more
  synthetic-only plumbing

### Current Backend Integration Shape

The current live runtime flow is:

1. normalize one user turn
2. split it into sentence-like segments with `pySBD` when available and regex
   fallback otherwise
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
- the preferred runtime splitter depends on `pysbd` being present in the app
  environment; otherwise the backend falls back to regex segmentation
- `importance` remains policy metadata; it is not a direct classifier output
