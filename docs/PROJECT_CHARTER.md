# Project Charter

## English

### Purpose

CareerGuide is an academic proof-of-concept web application that helps users explore career paths, skill gaps, role progression, and work-life balance considerations through grounded AI assistance.

### Academic Context

The project should reflect the student’s education in artificial intelligence and business. The implementation and documentation should be strong enough to serve as a final academic demonstration of both technical competence and practical product reasoning.

The student’s strongest academic background is in recurrent neural networks, especially LSTM. The Hopfield-style memory system is therefore not an arbitrary add-on. It is the project’s main novelty mechanism and the conceptual bridge from the student’s recurrent-network background into a modern personalized RAG system.

### Core Thesis Claim

The defensible claim of the project is:

> A grounded career-guidance assistant can be improved by combining hybrid RAG with a lightweight Hopfield-style associative memory layer that stores stable user preferences, goals, and constraints.

### Product Scope

The application should:

- be web-based
- focus on career guidance and work-life balance support
- use authoritative external sources for grounding
- personalize outputs with a lightweight memory layer
- produce outputs that the student can explain, inspect, and evaluate

### Non-Goals

The MVP should not drift into:

- Android or mobile-first product development
- unnecessary infrastructure complexity
- premature vector database adoption
- fine-tuning as a default path
- agent sprawl
- novelty claims that the implementation cannot defend

### Language and Stack Principles

- The end-user product experience should be Russian-first.
- English documentation should still be maintained for collaboration, review, and advisor access.
- Backend, ingestion, retrieval, evaluation, and orchestration should stay in Python unless a strong reason forces otherwise.
- Frontend work should stay in JavaScript or TypeScript.
- Durable documentation must be maintained in both English and Russian.
- Code identifiers should remain in English for consistency.

### Definition of Success

The project is successful when it demonstrates:

- grounded answers from authoritative career and wellbeing sources
- understandable architecture and readable code
- measurable personalization improvement from the memory layer
- academically honest framing of the Hopfield-style contribution
- clear documentation that supports student learning and project defense

## Русский

### Назначение

CareerGuide - это академическое proof-of-concept веб-приложение, которое помогает пользователям исследовать карьерные траектории, пробелы в навыках, карьерный рост и аспекты work-life balance с помощью grounded AI assistance.

### Академический контекст

Проект должен отражать образование студентки в областях искусственного интеллекта и бизнеса. Реализация и документация должны быть достаточно сильными, чтобы выступать итоговой академической демонстрацией как технической компетентности, так и практического продуктового мышления.

Самая сильная академическая база студентки связана с рекуррентными нейронными сетями, особенно с LSTM. Поэтому Hopfield-style memory system не является случайным дополнением. Это главный механизм новизны проекта и концептуальный мост от ее бэкграунда в recurrent networks к современной персонализированной RAG-системе.

### Основной тезис работы

Защищаемый тезис проекта звучит так:

> Grounded career-guidance assistant может быть улучшен за счет сочетания hybrid RAG и облегченного Hopfield-style associative memory layer, который хранит устойчивые пользовательские предпочтения, цели и ограничения.

### Границы продукта

Приложение должно:

- быть веб-ориентированным
- фокусироваться на карьерном сопровождении и поддержке work-life balance
- использовать авторитетные внешние источники для grounding
- персонализировать ответы с помощью облегченного memory layer
- выдавать результаты, которые студентка может объяснить, проверить и оценить

### Что не входит в MVP

MVP не должен уходить в:

- Android или mobile-first разработку
- избыточную инфраструктурную сложность
- преждевременное внедрение vector database
- fine-tuning как путь по умолчанию
- избыточное разрастание agent-архитектуры
- заявления о новизне, которые реализация не может защитить

### Принципы по языкам и стеку

- Пользовательский опыт продукта должен быть в первую очередь русскоязычным.
- Английская документация при этом должна сохраняться для совместной работы, ревью и доступа со стороны научного руководителя или технических участников.
- Backend, ingestion, retrieval, evaluation и orchestration должны оставаться на Python, если только сильная техническая причина не вынуждает к иному решению.
- Frontend должен оставаться на JavaScript или TypeScript.
- Долговечная документация должна поддерживаться на английском и русском языках.
- Идентификаторы в коде должны оставаться на английском языке ради единообразия.

### Критерии успеха

Проект считается успешным, если он демонстрирует:

- grounded-ответы на основе авторитетных карьерных и wellbeing-источников
- понятную архитектуру и читаемый код
- измеримое улучшение персонализации за счет memory layer
- академически корректное позиционирование Hopfield-style вклада
- ясную документацию, поддерживающую обучение студентки и защиту проекта
