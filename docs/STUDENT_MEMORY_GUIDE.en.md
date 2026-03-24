# Student Memory Guide

Last updated: 2026-03-24

## 1. Why This Document Exists

This document is narrower than the general student manual.

Its purpose is to help the student focus on the part of the project that most
directly matches her academic background:

- recurrent neural networks
- LSTM and BiLSTM sequence modeling
- memory systems

In this project, that background maps directly onto two concrete subsystems:

1. **BiLSTM sentence classification** for deciding whether a user sentence
   should be kept as memory
2. **Hopfield-style memory recall** for deciding which stored memories matter
   later when answering a new question

The student does **not** need to master every implementation detail in the
whole application to defend the project well.

She does need to understand the memory subsystem deeply enough to:

- explain what it does
- explain why it is academically relevant
- explain how it integrates into the product
- retrain and improve it
- propose defensible next experiments

## 2. The Student’s Role In This Project

The student’s most defensible “ownership area” is the memory system.

That means her strongest contribution can be framed like this:

> The system uses a supervised recurrent-network classifier to decide what user
> information is stable enough to remember, and a Hopfield-style associative
> memory mechanism to recall the most relevant stored information later.

This is a strong role because it is:

- technically real
- directly connected to the deployed system
- aligned with her studies
- easy to explain in both product and ML terms

If the professor asks, “What part of this system is most related to the
student’s own specialization?”, the answer should be:

> The memory subsystem, especially BiLSTM memory extraction and Hopfield-style
> recall.

## 3. What The Memory System Does

The memory system has two separate jobs.

### 3.1 Job A: Decide What To Remember

When the user sends a message, the system does **not** store the entire
message blindly.

Instead it:

1. splits the message into sentence-like segments
2. classifies each segment as `MEMORY` or `NO_MEMORY`
3. keeps only the segments that pass the classifier and threshold
4. deduplicates them
5. stores them in persistent memory

This is the **memory creation** side of the system.

### 3.2 Job B: Decide Which Stored Memories Matter Later

When the user asks a new question later, the system:

1. loads stored memory items for that user
2. embeds the new question
3. embeds stored memory texts
4. scores question-to-memory similarity
5. performs a Hopfield-style associative recall step
6. summarizes the top recalled memories into the grounded prompt

This is the **memory recall** side of the system.

## 4. Where The Memory System Lives In Code

These are the most important files.

### Runtime Memory Creation

- [`backend/app/services/memory/sentence_split.py`](../backend/app/services/memory/sentence_split.py)
  Splits a user turn into sentence-like segments.
- [`backend/app/services/memory/runtime_classifier.py`](../backend/app/services/memory/runtime_classifier.py)
  Loads the trained classifier bundle and runs inference.
- [`backend/app/services/memory/memory_extract.py`](../backend/app/services/memory/memory_extract.py)
  Turns accepted segments into `MemoryItemPayload` objects.
- [`backend/app/services/memory/memory_consolidate.py`](../backend/app/services/memory/memory_consolidate.py)
  Deduplicates memory candidates by normalized text.
- [`backend/app/services/memory/memory_store.py`](../backend/app/services/memory/memory_store.py)
  Persists memory items in SQLite.

### Memory Recall

- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)
  Performs the associative memory recall.

### Integration

- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)
  Stages memory before answer generation, previews it for the current turn, and
  only persists it after a successful non-refusal answer.

### Training Tooling

- [`tooling/memory_extraction/generate_synthetic_dataset.py`](../tooling/memory_extraction/generate_synthetic_dataset.py)
- [`tooling/memory_extraction/prepare_dataset.py`](../tooling/memory_extraction/prepare_dataset.py)
- [`tooling/memory_extraction/train_bilstm_classifier.py`](../tooling/memory_extraction/train_bilstm_classifier.py)
- [`tooling/memory_extraction/evaluate_classifier.py`](../tooling/memory_extraction/evaluate_classifier.py)
- [`tooling/memory_extraction/classifier.py`](../tooling/memory_extraction/classifier.py)

## 5. How Memory Creation Works

### 5.1 Sentence Splitting

The first step is segmentation.

The runtime prefers `pySBD` and falls back to regex splitting if `pysbd` is not
installed. This happens in:

- [`backend/app/services/memory/sentence_split.py`](../backend/app/services/memory/sentence_split.py)

The system also:

- collapses whitespace
- removes list/bullet prefixes
- does light language detection between Russian and English

This matters because the classifier expects a short sentence-like input, not a
whole paragraph.

### 5.2 BiLSTM Classification

The classifier logic lives in:

- [`tooling/memory_extraction/classifier.py`](../tooling/memory_extraction/classifier.py)

The current baseline is a lightweight **BiLSTM classifier**:

- tokenization with a Unicode-aware regex
- learned token embeddings
- bidirectional LSTM encoder
- linear classification head

Why BiLSTM is a good fit here:

- the task is sentence classification
- order matters
- small local training is realistic
- the architecture is directly connected to the student’s coursework

### 5.3 Runtime Thresholding

The classifier does not automatically store every positive prediction.

The runtime also applies:

- minimum segment length
- minimum confidence threshold

These settings live in:

- [`backend/app/config.py`](../backend/app/config.py)

Important values to know:

- `memory_extraction_backend`
- `memory_extraction_model_path`
- `memory_extraction_min_confidence`
- `memory_extraction_default_category`
- `memory_extraction_default_importance`

### 5.4 Staging Before Persistence

One of the most important design decisions is this:

> New memory is staged first and only persisted after a successful non-refusal
> answer.

Why this matters:

- refused requests should not teach the system new memory
- exploitative or unsupported requests should not pollute persistent memory
- the current turn can still preview candidate memory before commit

This logic lives in:

- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)

## 6. How Hopfield Recall Works

The recall logic lives in:

- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)

The current implementation is intentionally honest and readable.

It is:

- embedding-based
- non-trainable
- explicit about scores and weights
- available in `top1` and `topk` modes

### 6.1 What Happens

For a new question:

1. embed the question
2. embed stored memory texts
3. compute dot-product scores
4. convert scores into softmax-like weights
5. choose the best memory (`top1`) or a small weighted set (`topk`)
6. return an inspectable recall result

### 6.2 What To Say Academically

A good explanation is:

> The current system uses a practical Hopfield-style associative recall step in
> embedding space. It is not yet the final learned differentiable phase, but it
> already implements the key idea of content-addressable memory recall over
> stored user-memory vectors.

What **not** to claim:

- do not say the project invented a new neural architecture
- do not say the current repo already has learned Hopfield projections
- do not say the current implementation already includes differentiable
  `ksoftmax`

## 7. How This Integrates Into The Full App

This is the simplest high-level explanation.

### Chat Request

1. user sends question
2. system stages memory candidates
3. system recalls relevant stored memory
4. system retrieves ESCO evidence
5. system builds the grounded prompt
6. system answers
7. system persists staged memory only if the answer succeeded

So memory affects both:

- what gets stored for the future
- what gets recalled for the present answer

### Why This Is Good For The Thesis

This gives the student a clear story:

- retrieval handles external knowledge
- generation handles answer phrasing
- memory handles stable personalization

That separation is much easier to defend than a vague “the LLM somehow knows
the user.”

## 8. Current Trained Baseline

The tracked runtime bundle is:

- [`tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`](../tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt)

The current data/training pipeline already supports:

- synthetic bilingual data generation
- binary split preparation
- BiLSTM training
- held-out evaluation

The current baseline is intentionally **binary first**:

- `MEMORY`
- `NO_MEMORY`

This is the right first runtime decision because the system first needs to know
whether a sentence is worth storing at all.

## 9. How To Retrain The Memory Classifier

Use the tooling in [`tooling/memory_extraction/`](../tooling/memory_extraction/README.md).

### 9.1 Generate Or Refresh The Raw Corpus

Example:

```bash
python -m tooling.memory_extraction.generate_synthetic_dataset \
  --model-source /path/to/Qwen3-0.6B-Transformers \
  --device cuda \
  --dtype float16 \
  --seed 17 \
  --batch-size 32 \
  --max-tokens 64 \
  --examples-per-label 250 \
  --output-jsonl tooling/memory_extraction/data/synthetic_memory_sentences_v4.jsonl
```

### 9.2 Prepare The Binary Splits

```bash
python -m tooling.memory_extraction.prepare_dataset \
  --task binary \
  --input-jsonl tooling/memory_extraction/data/synthetic_memory_sentences_v4.jsonl
```

### 9.3 Train The BiLSTM

```bash
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
```

### 9.4 Evaluate It

```bash
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

### 9.5 Replace The Runtime Bundle

The backend loads the runtime classifier from:

- [`backend/app/config.py`](../backend/app/config.py)
- setting: `memory_extraction_model_path`

If you train a better bundle, you can:

- replace the tracked default bundle
- or point the runtime to a new path

## 10. How The Student Should Explain Retraining

If asked “How would you improve this system?”, the student should say something
like:

> The current classifier is a small bilingual BiLSTM trained first on
> synthetic data. The next improvement path is to replace or augment that
> synthetic supervision with dialogue-based preference data and manually labeled
> negative examples, then retrain and compare the new classifier against the
> current baseline.

That is much stronger than saying “I would tweak the prompt.”

## 11. Suggested Exercises For The Student

These exercises are realistic and directly connected to the live system.

### Exercise 1: Train A Better Binary Memory Classifier

Goal:

- improve `MEMORY` vs `NO_MEMORY`

What to change:

- use better training data
- add real dialogue-derived examples
- improve label quality
- compare threshold behavior on Russian and English

Success criteria:

- better held-out macro-F1
- better Russian negative recall
- fewer obvious false positives on casual chat

### Exercise 2: Train A Multi-Class Memory Type Classifier

Goal:

- classify positive memory into:
  - `PREFERENCE`
  - `CONSTRAINT`
  - `GOAL`
  - `AVAILABILITY`

Recommended architecture:

- keep the binary model as stage one
- add a second classifier only for positive memory sentences

Why this is better than a one-shot five-way classifier:

- it keeps the main store-or-not-store decision stable
- it reduces the risk that noisy type boundaries hurt the storage decision
- it is easier to explain experimentally

### Exercise 3: Threshold Calibration Study

Goal:

- study how `memory_extraction_min_confidence` changes false positives and false negatives

Why this is useful:

- it is small enough for a student project
- it directly changes live runtime behavior
- it is easy to explain to professors

### Exercise 4: Compare Memory Recall Modes

Goal:

- compare Hopfield `top1` vs `topk` on chosen demo cases

Why this matters:

- it directly connects the memory mechanism to the product behavior
- it supports the thesis narrative better than generic UX changes

## 12. Better Data Sources Than Pure Synthetic Data

The synthetic dataset was a practical starting point, not the final ideal data
source.

### LAPS

The user-referenced LAPS repository is a strong candidate:

- GitHub: [informagi/laps](https://github.com/informagi/laps)

Why it is relevant:

- it contains **multi-session conversational dialogues**
- it contains **extracted actual user preferences**
- it includes structured dialogue/session information
- it is much closer to real conversational preference signals than purely
  synthetic single sentences

According to the repository README, LAPS includes:

- recipe and movie domains
- train/validation/test splits
- session dialogues
- extracted preference fields
- task-setting metadata

That makes it useful for memory research even though it is not a perfect
drop-in dataset for this exact app.

### How To Use LAPS For This Project

Do **not** assume it can be used without preprocessing.

A sensible approach would be:

1. extract only the **user-side utterances**
2. align each utterance with the known preference state of that session
3. convert the data into sentence-level classification records
4. label sentences that express stable preference or constraint information as
   positive memory candidates
5. create explicit `NO_MEMORY` negatives from task chatter, coordination turns,
   filler, and other non-stable sentences

For the multi-class setting, you would also need a project-specific mapping
from LAPS preference information into labels such as:

- `PREFERENCE`
- `CONSTRAINT`
- `GOAL`
- `AVAILABILITY`

That mapping will require manual design and probably manual review.

### Another Strong Option

The student can also create a small hand-labeled in-domain corpus from real app
dialogues or simulated project-specific career chats.

This is attractive because:

- it matches the actual app domain
- the label design can be tailored to this project
- it is easy to justify academically as domain adaptation

## 13. A Good Defense Story For Professors

If the student needs to explain the memory part clearly, this is a good
structure:

1. The assistant should not store every sentence blindly.
2. So the system first uses a supervised BiLSTM classifier to detect memory-worthy sentences.
3. The accepted sentences are stored persistently in SQLite.
4. Later, when answering new questions, the system recalls the most relevant
   stored memory through a Hopfield-style associative step over embeddings.
5. This makes personalization explicit and inspectable.

Why this is a strong explanation:

- it is technically specific
- it is honest
- it matches the live code
- it aligns with the student’s coursework

## 14. What The Student Does Not Need To Master

The student does **not** need to fully master all of this to defend the memory
system well:

- every frontend CSS detail
- every retrieval benchmark setting
- every generation prompt nuance
- every operator script in the repo

She should instead be strongest on:

- the BiLSTM classifier
- the memory data pipeline
- the storage decision
- the Hopfield recall mechanism
- the improvement roadmap for memory

## 15. Final Recommendation

If the student has limited time, her best path is:

1. understand the current memory flow end-to-end
2. retrain the binary BiLSTM once
3. study whether better data improves it
4. propose or prototype a second-stage multi-class memory classifier

That is enough to create a strong and defensible personal contribution inside a
larger sophisticated system.
