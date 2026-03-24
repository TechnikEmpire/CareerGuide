# Project Charter

### Purpose

CareerGuide is an academic proof-of-concept web application that helps users explore career paths, skill gaps, role progression, and work-life balance considerations through grounded AI assistance.

### Academic Context

The project should reflect the student’s education in artificial intelligence and business. The implementation and documentation should be strong enough to serve as a final academic demonstration of both technical competence and practical product reasoning.

The student's strongest academic background is in recurrent neural networks, especially LSTM. The Hopfield memory system is therefore not an arbitrary add-on. It is the project's main novelty mechanism and the conceptual bridge from the student's recurrent-network background into a modern personalized RAG system. The defended target is a real learned Hopfield-style memory module with explicit `top1` and `topk` recall modes, not merely a similarity-ranking helper.

### Core Thesis Claim

The defensible claim of the project is:

> A grounded career-guidance assistant can be improved by combining dense ANN-backed RAG with a small learned Hopfield-style memory module that stores stable user preferences, goals, and constraints and supports both `top1` and `topk` recall regimes.

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
- academically honest framing of the Hopfield contribution as a real learned memory-retrieval mechanism rather than a naming trick
- clear documentation that supports student learning and project defense
