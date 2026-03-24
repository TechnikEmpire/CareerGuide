# Руководство для студентки по memory-системе

Последнее обновление: 2026-03-24

## 1. Зачем нужен именно этот документ

Этот документ уже, чем общий student manual.

Его цель — помочь студентке сосредоточиться на той части проекта, которая
наиболее прямо совпадает с ее академическим бэкграундом:

- recurrent neural networks
- LSTM и BiLSTM sequence modeling
- memory systems

В этом проекте такой бэкграунд напрямую соответствует двум конкретным
подсистемам:

1. **BiLSTM sentence classification** для решения, стоит ли сохранять
   пользовательскую фразу как memory
2. **Hopfield-style memory recall** для решения, какие уже сохраненные memory
   важны позже при ответе на новый вопрос

Студентке **не** нужно идеально понимать каждую деталь всей системы, чтобы
хорошо защитить проект.

Зато ей нужно достаточно глубоко понимать memory-subsystem, чтобы:

- объяснить, что он делает
- объяснить, почему он академически релевантен
- объяснить, как он встроен в продукт
- переобучить и улучшить его
- предложить защищаемые следующие эксперименты

## 2. Роль студентки в этом проекте

Самая защищаемая зона «владения» студентки — это memory-system.

Эту роль можно формулировать так:

> Система использует supervised recurrent-network classifier, чтобы решить,
> какая пользовательская фраза достаточно стабильна для сохранения в память, и
> Hopfield-style associative memory mechanism, чтобы позже вызывать наиболее
> релевантную сохраненную информацию.

Это сильная роль, потому что она:

- технически реальна
- напрямую связана с deployed system
- согласована с ее учебой
- легко объясняется и на языке продукта, и на языке ML

Если профессор спросит: «Какая часть системы наиболее связана со
специализацией студентки?», ответ должен быть таким:

> Memory-subsystem, особенно BiLSTM memory extraction и Hopfield-style recall.

## 3. Что делает memory-system

У memory-system есть две отдельные задачи.

### 3.1 Задача A: решить, что запоминать

Когда пользователь отправляет сообщение, система **не** сохраняет весь текст
слепо.

Вместо этого она:

1. разбивает сообщение на sentence-like segments
2. классифицирует каждый segment как `MEMORY` или `NO_MEMORY`
3. оставляет только те segments, которые прошли classifier и threshold
4. дедуплицирует их
5. сохраняет их в persistent memory

Это сторона **создания памяти**.

### 3.2 Задача B: решить, какая память важна позже

Когда пользователь потом задает новый вопрос, система:

1. загружает сохраненные memory items для этого пользователя
2. создает embedding нового вопроса
3. создает embeddings для сохраненных memory texts
4. считает similarity-score между вопросом и memory
5. выполняет Hopfield-style associative recall step
6. суммирует top recalled memories в grounded prompt

Это сторона **вызова памяти**.

## 4. Где memory-system находится в коде

Это самые важные файлы.

### Runtime memory creation

- [`backend/app/services/memory/sentence_split.py`](../backend/app/services/memory/sentence_split.py)
  Разбивает user turn на sentence-like segments.
- [`backend/app/services/memory/runtime_classifier.py`](../backend/app/services/memory/runtime_classifier.py)
  Загружает trained classifier bundle и запускает inference.
- [`backend/app/services/memory/memory_extract.py`](../backend/app/services/memory/memory_extract.py)
  Превращает принятые segments в `MemoryItemPayload`.
- [`backend/app/services/memory/memory_consolidate.py`](../backend/app/services/memory/memory_consolidate.py)
  Дедуплицирует memory-candidates по normalized text.
- [`backend/app/services/memory/memory_store.py`](../backend/app/services/memory/memory_store.py)
  Сохраняет memory items в SQLite.

### Memory recall

- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)
  Выполняет associative recall.

### Интеграция

- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)
  Делает staging памяти до answer-generation, preview для текущего turn и
  сохраняет ее только после успешного non-refusal answer.

### Training tooling

- [`tooling/memory_extraction/generate_synthetic_dataset.py`](../tooling/memory_extraction/generate_synthetic_dataset.py)
- [`tooling/memory_extraction/prepare_dataset.py`](../tooling/memory_extraction/prepare_dataset.py)
- [`tooling/memory_extraction/train_bilstm_classifier.py`](../tooling/memory_extraction/train_bilstm_classifier.py)
- [`tooling/memory_extraction/evaluate_classifier.py`](../tooling/memory_extraction/evaluate_classifier.py)
- [`tooling/memory_extraction/classifier.py`](../tooling/memory_extraction/classifier.py)

## 5. Как работает создание памяти

### 5.1 Sentence splitting

Первый шаг — сегментация.

Runtime предпочитает `pySBD` и откатывается к regex-splitting, если `pysbd`
не установлен. Это происходит в:

- [`backend/app/services/memory/sentence_split.py`](../backend/app/services/memory/sentence_split.py)

Система также:

- схлопывает whitespace
- убирает list/bullet prefixes
- делает легкое language-detection между русским и английским

Это важно, потому что classifier ожидает короткий sentence-like input, а не
целый абзац.

### 5.2 BiLSTM classification

Логика classifier находится в:

- [`tooling/memory_extraction/classifier.py`](../tooling/memory_extraction/classifier.py)

Текущий baseline — это легкий **BiLSTM-classifier**:

- tokenization через Unicode-aware regex
- обучаемые token embeddings
- bidirectional LSTM encoder
- linear classification head

Почему BiLSTM здесь хорошо подходит:

- задача является sentence classification
- порядок токенов важен
- маленькое локальное обучение реалистично
- архитектура напрямую связана с учебной программой студентки

### 5.3 Runtime thresholding

Classifier не сохраняет автоматически каждый positive prediction.

Runtime также применяет:

- minimum segment length
- minimum confidence threshold

Эти настройки находятся в:

- [`backend/app/config.py`](../backend/app/config.py)

Ключевые значения:

- `memory_extraction_backend`
- `memory_extraction_model_path`
- `memory_extraction_min_confidence`
- `memory_extraction_default_category`
- `memory_extraction_default_importance`

### 5.4 Staging перед сохранением

Одно из самых важных design-decisions звучит так:

> Новая memory сначала попадает в staging и сохраняется только после успешного
> non-refusal answer.

Почему это важно:

- refused requests не должны обучать систему новой памяти
- exploitative и unsupported requests не должны загрязнять persistent memory
- текущий turn все еще может preview-ить candidate-memory до commit

Эта логика находится в:

- [`backend/app/services/assistant_service.py`](../backend/app/services/assistant_service.py)

## 6. Как работает Hopfield recall

Логика recall находится в:

- [`backend/app/services/memory/hopfield_memory.py`](../backend/app/services/memory/hopfield_memory.py)

Текущая реализация намеренно честная и читаемая.

Она:

- embedding-based
- non-trainable
- явно показывает scores и weights
- поддерживает режимы `top1` и `topk`

### 6.1 Что именно происходит

Для нового вопроса:

1. создается embedding вопроса
2. создаются embeddings сохраненных memory-texts
3. считаются dot-product scores
4. scores переводятся в softmax-like weights
5. выбирается либо лучшая память (`top1`), либо небольшой weighted set (`topk`)
6. возвращается inspectable result recall

### 6.2 Как это объяснять академически

Хорошая формулировка такая:

> Текущая система использует практический Hopfield-style associative recall step
> в embedding-space. Это еще не финальная learned differentiable phase, но уже
> реализует ключевую идею content-addressable memory recall поверх сохраненных
> user-memory vectors.

Чего **не** нужно утверждать:

- не говорите, что проект изобрел новую neural architecture
- не говорите, что в repo уже есть learned Hopfield projections
- не говорите, что текущая реализация уже включает differentiable `ksoftmax`

## 7. Как это встраивается в полное приложение

Самое простое high-level explanation такое.

### Chat request

1. пользователь отправляет вопрос
2. система staging-ом извлекает memory-candidates
3. система вызывает релевантную сохраненную память
4. система извлекает ESCO evidence
5. система строит grounded prompt
6. система отвечает
7. система сохраняет staged memory только если answer был успешным

Итак, memory влияет и на:

- то, что будет сохранено для будущего
- то, что будет вызвано для текущего ответа

### Почему это хорошо для thesis

Это дает студентке ясную историю:

- retrieval отвечает за внешнее знание
- generation отвечает за формулировку ответа
- memory отвечает за устойчивую персонализацию

Такое разделение гораздо легче защищать, чем расплывчатую идею «LLM somehow
knows the user».

## 8. Текущий обученный baseline

Отслеживаемый runtime-bundle:

- [`tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt`](../tooling/memory_extraction/models/bilstm_memory_classifier_binary.pt)

Текущий data/training-pipeline уже поддерживает:

- synthetic bilingual data generation
- binary split preparation
- BiLSTM training
- held-out evaluation

Текущий baseline намеренно **binary first**:

- `MEMORY`
- `NO_MEMORY`

Это правильное первое runtime-решение, потому что системе сначала нужно
понять, стоит ли вообще сохранять фразу как memory.

## 9. Как переобучить memory-classifier

Используйте tooling в [`tooling/memory_extraction/`](../tooling/memory_extraction/README.md).

### 9.1 Сгенерировать или обновить raw corpus

Пример:

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

### 9.2 Подготовить binary splits

```bash
python -m tooling.memory_extraction.prepare_dataset \
  --task binary \
  --input-jsonl tooling/memory_extraction/data/synthetic_memory_sentences_v4.jsonl
```

### 9.3 Обучить BiLSTM

```bash
python -m tooling.memory_extraction.train_bilstm_classifier --task binary
```

### 9.4 Оценить его

```bash
python -m tooling.memory_extraction.evaluate_classifier --task binary
```

### 9.5 Заменить runtime bundle

Backend загружает runtime-classifier из:

- [`backend/app/config.py`](../backend/app/config.py)
- setting: `memory_extraction_model_path`

Если вы обучили лучший bundle, можно:

- заменить tracked default bundle
- или указать runtime на новый path

## 10. Как студентке объяснять переобучение

Если вас спросят: «Как бы вы улучшили эту систему?», студентка должна
говорить примерно так:

> Текущий classifier — это небольшой bilingual BiLSTM, сначала обученный на
> synthetic data. Следующий путь улучшения — заменить или дополнить synthetic
> supervision диалоговыми preference-data и вручную размеченными negative
> examples, а затем переобучить модель и сравнить ее с текущим baseline.

Это намного сильнее, чем просто сказать: «Я бы подкрутила prompt».

## 11. Рекомендуемые упражнения для студентки

Эти упражнения реалистичны и напрямую связаны с live-system.

### Упражнение 1: обучить более сильный binary memory-classifier

Цель:

- улучшить `MEMORY` vs `NO_MEMORY`

Что менять:

- использовать более качественные training-data
- добавить real dialogue-derived examples
- улучшить качество labels
- сравнить threshold-behavior на русском и английском

Критерии успеха:

- лучший held-out macro-F1
- лучший Russian negative recall
- меньше очевидных false positives в casual chat

### Упражнение 2: обучить multi-class classifier для type-memory

Цель:

- классифицировать positive memory по типам:
  - `PREFERENCE`
  - `CONSTRAINT`
  - `GOAL`
  - `AVAILABILITY`

Рекомендуемая архитектура:

- оставить binary model как первый stage
- добавить второй classifier только для positive memory sentences

Почему это лучше, чем one-shot five-way classifier:

- сохраняет стабильность главного решения «store or not store»
- снижает риск того, что шумные type-boundaries испортят решение о сохранении
- эксперимент проще объяснять

### Упражнение 3: исследование threshold calibration

Цель:

- изучить, как `memory_extraction_min_confidence` меняет false positives и false negatives

Почему это полезно:

- достаточно мало по объему для student project
- напрямую меняет live runtime behavior
- это легко объяснить профессорам

### Упражнение 4: сравнить memory recall modes

Цель:

- сравнить Hopfield `top1` и `topk` на выбранных demo-cases

Почему это важно:

- это напрямую связывает memory-mechanism с product behavior
- это лучше поддерживает thesis narrative, чем общие UX-изменения

## 12. Более качественные источники данных, чем чисто synthetic data

Synthetic dataset был удобной отправной точкой, но не идеальным финальным
источником данных.

### LAPS

LAPS, на который сослался пользователь, — очень хороший кандидат:

- GitHub: [informagi/laps](https://github.com/informagi/laps)

Почему он релевантен:

- содержит **multi-session conversational dialogues**
- содержит **extracted actual user preferences**
- включает структурированную session/dialogue информацию
- гораздо ближе к реальным conversational preference signals, чем purely synthetic single sentences

Согласно README репозитория, LAPS включает:

- domains recipe и movie
- train/validation/test splits
- session dialogues
- extracted preference fields
- task-setting metadata

Это делает dataset полезным для memory-research, даже если он не является
идеальным drop-in dataset для именно этого приложения.

### Как использовать LAPS в этом проекте

**Не** считайте, что его можно использовать без preprocessing.

Разумный подход такой:

1. взять только **user-side utterances**
2. сопоставить каждую utterance с известным preference-state этой session
3. преобразовать данные в sentence-level classification records
4. размечать предложения, выражающие устойчивое preference или constraint information, как positive memory candidates
5. создавать явные `NO_MEMORY` negatives из task chatter, coordination turns, filler и других нестабильных предложений

Для multi-class setting также потребуется project-specific mapping из LAPS
preference-information в labels вроде:

- `PREFERENCE`
- `CONSTRAINT`
- `GOAL`
- `AVAILABILITY`

Такой mapping потребует ручного дизайна и, вероятно, ручной проверки.

### Еще один сильный вариант

Студентка также может создать небольшой hand-labeled in-domain corpus из
реальных app-dialogues или специально смоделированных career-chat диалогов.

Это привлекательно, потому что:

- такие данные совпадают с реальным domain приложения
- design labels можно адаптировать именно под этот проект
- академически это легко защищать как domain adaptation

## 13. Хорошая история для защиты перед профессорами

Если студентке нужно ясно объяснить memory-part, хорошая структура такая:

1. Ассистент не должен слепо сохранять каждое предложение.
2. Поэтому система сначала использует supervised BiLSTM-classifier для
   detection memory-worthy sentences.
3. Принятые предложения сохраняются persistently в SQLite.
4. Позже, при ответе на новые вопросы, система вызывает наиболее релевантную
   память через Hopfield-style associative step поверх embeddings.
5. Это делает personalization явной и inspectable.

Почему это сильное объяснение:

- оно технически конкретно
- оно честно
- оно соответствует live-code
- оно согласовано с coursework студентки

## 14. Что студентке не нужно знать идеально

Студентке **не** нужно идеально разбираться во всем этом, чтобы хорошо
защищать memory-system:

- в каждой детали frontend CSS
- в каждом retrieval benchmark setting
- в каждом нюансе generation prompt
- в каждом operator script репозитория

Вместо этого ей лучше всего быть сильной в:

- BiLSTM-classifier
- memory data pipeline
- decision logic для хранения
- Hopfield recall mechanism
- roadmap улучшения memory-system

## 15. Финальная рекомендация

Если у студентки мало времени, лучший путь такой:

1. понять текущий memory-flow end-to-end
2. один раз переобучить binary BiLSTM
3. изучить, улучшают ли более качественные данные результат
4. предложить или прототипировать second-stage multi-class memory-classifier

Этого уже достаточно, чтобы сформировать сильный и защищаемый личный вклад
внутри более крупной и сложной системы.
