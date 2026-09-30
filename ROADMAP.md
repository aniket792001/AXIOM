# Project Roadmap: Axiom & SCORE Engine

> **Mission**: Build, benchmark, and deploy a production-grade, zero-hallucination agentic RAG platform for high-stakes enterprise data.

---

## 🗺️ High-Level Milestone Overview

```mermaid
gantt
    title Axiom & SCORE Production Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1: Foundation
    Brand & Architecture Spec :done, p1_1, 2026-10-01, 2026-10-02
    Domain Context & Tech Stack Specs :done, p1_2, 2026-10-02, 2026-10-03
    section Phase 2: Scaffolding
    Repo Layout & pyproject.toml :active, p2_1, 2026-10-03, 2026-10-05
    Pydantic Settings & Config :active, p2_2, 2026-10-04, 2026-10-06
    section Phase 3: Core Engine
    Typed AgentState Schema :p3_1, 2026-10-06, 2026-10-08
    Grader, Router & Rewriter Nodes :p3_2, 2026-10-08, 2026-10-12
    LangGraph Compilation & Loops :p3_3, 2026-10-12, 2026-10-15
    section Phase 4: Retrieval Services
    Hybrid Search (Dense + BM25) :p4_1, 2026-10-15, 2026-10-18
    Cross-Encoder Re-ranker :p4_2, 2026-10-18, 2026-10-20
    section Phase 5: API & Streaming
    FastAPI Endpoints & Schemas :p5_1, 2026-10-20, 2026-10-23
    Server-Sent Events (SSE) Engine :p5_2, 2026-10-23, 2026-10-26
    section Phase 6: Evals & Benchmark
    Golden Contract & 10-K Dataset :p6_1, 2026-10-26, 2026-10-29
    Automated Ragas CI/CD Suite :p6_2, 2026-10-29, 2026-11-02
    section Phase 7: UI & Production Ops
    Enterprise Verification UI :p7_1, 2026-11-02, 2026-11-06
    Docker, Redis Checkpointing & Deploy :p7_2, 2026-11-06, 2026-11-10
```

---

## 📌 Phase Breakdown

### Phase 1: Foundation & Specifications `[COMPLETED]`
- [x] Lock in Brand Identity (**Axiom**) and Engine Name (**SCORE**).
- [x] Finalize Semantic Color Tokens and Design Guidelines.
- [x] Author Master Brand & Architecture Spec (`AXIOM_FOUNDATION.md` & `docs/brand_and_architecture_spec.md`).
- [x] Document Domain Context (`CONTEXT.md`) and Technical Justifications (`TECH_STACK.md`).
- [x] Establish AI portability rules (`AGENTS.md`) and Architecture Decision Records (`DECISIONS.md`).

### Phase 2: Scaffolding & Configuration `[CURRENT]`
- [ ] Create production directory structure (`src/axiom/`, `tests/`, `evals/`, `deploy/`).
- [ ] Author `pyproject.toml` with pinned dependencies (`langgraph`, `fastapi`, `pydantic-settings`, `qdrant-client`).
- [ ] Build central configuration module (`src/axiom/config/settings.py`) with environment validation.
- [ ] Create `.env.example` with clear instructions for API keys.

### Phase 3: Core SCORE LangGraph Engine
- [ ] Define immutable typed state (`src/axiom/core/state.py`).
- [ ] Implement isolated node handlers:
  - `router.py`: Classifies query intent (internal vector store vs web search).
  - `grader.py`: Structured binary output relevance grader.
  - `rewriter.py`: Query reformulation for multi-hop expansion.
  - `generator.py`: Grounded response synthesizer with citation requirements.
  - `hallucination_grader.py`: Grounding audit against retrieved chunks.
  - `fallback.py`: Transparent refusal handler when retries expire.
- [ ] Assemble and compile the LangGraph state machine with loop ceiling guard ($\le 3$).

### Phase 4: Hybrid Ingestion & Retrieval Services
- [ ] Implement markdown-preserving tabular document parser.
- [ ] Build hybrid retriever combining dense vector embeddings and BM25 sparse index.
- [ ] Integrate cross-encoder re-ranking service (Cohere / BGE).
- [ ] Integrate Tavily / Google Search API as live web fallback.

### Phase 5: FastAPI Gateway & Real-Time SSE Streaming
- [ ] Setup FastAPI application factory with CORS and health probes.
- [ ] Implement `POST /api/v1/query` endpoint with Server-Sent Events (SSE).
- [ ] Stream real-time graph state events (`status`) alongside incremental tokens (`token`).
- [ ] Implement document upload and ingestion endpoint (`POST /api/v1/ingest`).

### Phase 6: Golden Benchmark Showcase & Automated Evals
- [ ] Assemble public contract dataset with tricky amendments and multi-hop clauses.
- [ ] Build synthetic evaluation test cases in `evals/golden_contracts.json`.
- [ ] Author automated Ragas evaluation runner (`evals/run_evals.py`).
- [ ] Enforce automated CI/CD gating: Faithfulness $\ge 0.95$.

### Phase 7: Interactive Verification Dashboard & Production Hardening
- [ ] Build responsive, high-density web UI adhering to Axiom design tokens.
- [ ] Display real-time step visualization (Node activations, discarded chunks, verified citations).
- [ ] Configure Redis / PostgreSQL persistent checkpointer (`AsyncPostgresSaver`).
- [ ] Author `docker-compose.yml` for zero-friction local orchestration.
