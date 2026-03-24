# Memory Extraction Tooling

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

Это tooling по-прежнему остается training- и evaluation-path для extraction
baseline, но отслеживаемый binary bundle теперь также питает live runtime-path
в `backend/app/services/memory/memory_extract.py`.

### Зачем это нужно

Live runtime теперь уже действительно использует отслеживаемый binary
BiLSTM-bundle для sentence-level extraction. Это tooling все равно остается
важным, потому что студентке нужен воспроизводимый путь улучшения модели, а не
отношение к текущему bundle как к чему-то окончательному.

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
- live-backend теперь уже использует tracked binary bundle в sentence-level
  memory write-path
- runtime sentence-splitting теперь предпочитает `pySBD` и откатывается к
  regex, если `pysbd` еще не установлен в app-env
- следующий runtime-шаг — это real-chat evaluation и debugging, а не еще один
  слой synthetic-only plumbing

### Текущая схема backend-интеграции

Текущий live runtime-flow такой:

1. нормализовать один user turn
2. разбить его на sentence-like segments через `pySBD`, когда он доступен, и
   через regex-fallback в противном случае
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
- preferred runtime-splitter зависит от наличия `pysbd` в app-env; в
  противном случае backend откатывается к regex-segmentation
- `importance` остается policy metadata; это не прямой output classifier
