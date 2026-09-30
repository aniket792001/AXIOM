# Axiom Execution Checklist (TODO.md)

> Track active implementation tasks across phases. Update task states as progress is made.

---

## Current Status: Phase 2 (Scaffolding & Configuration)

---

### Phase 1: Foundation & Brand Identity `[COMPLETED]`
- [x] Finalize Brand Name: **Axiom** (Platform) & **SCORE** (Engine).
- [x] Finalize Semantic Color Tokens and Design Guidelines.
- [x] Write Master Brand & Architecture Spec (`AXIOM_FOUNDATION.md` & `docs/brand_and_architecture_spec.md`).
- [x] Write `README.md` with architecture diagrams and overview.
- [x] Write `CONTRIBUTING.md` with coding and PR standards.
- [x] Write `CONTEXT.md` with domain manifesto and golden benchmark scenario.
- [x] Write `TECH_STACK.md` with architectural justifications.
- [x] Write `ROADMAP.md` with 7-phase timeline.
- [x] Write `AGENTS.md` for AI tool portability and context preservation.
- [x] Write `DECISIONS.md` (ADRs).

---

### Phase 2: Scaffolding & Configuration `[IN PROGRESS]`
- [ ] Create core directory tree (`src/axiom/`, `tests/`, `evals/`, `deploy/`).
- [ ] Create `pyproject.toml` with pinned dependencies:
  - `langgraph`, `langchain`, `langchain-community`, `langchain-openai` / `langchain-google-genai`
  - `fastapi`, `uvicorn`, `sse-starlette`, `pydantic`, `pydantic-settings`
  - `qdrant-client`, `chromadb`, `rank-bm25`, `cohere`
  - `ragas`, `pytest`, `ruff`, `mypy`
- [ ] Create `.env.example` with documented keys and configurations.
- [ ] Create `src/axiom/config/settings.py` using Pydantic Settings v2.
- [ ] Validate virtual environment and dependency installation.

---

### Phase 3: Core SCORE LangGraph State Machine `[PLANNED]`
- [ ] Author `src/axiom/core/state.py` with typed `AgentState` schema:
  - `query: str`
  - `rewritten_query: Optional[str]`
  - `documents: List[Document]`
  - `graded_documents: List[Document]`
  - `generation: str`
  - `citations: List[Citation]`
  - `loop_count: int`
  - `reasoning_trace: List[StepEvent]`
- [ ] Author prompts in `src/axiom/core/prompts/`:
  - `router.md`: Classify vector vs web intent.
  - `grader.md`: Strict binary document relevance scoring.
  - `rewriter.md`: Query reformulation for multi-hop expansion.
  - `generator.md`: Citation-grounded synthesis with epistemic humility.
  - `hallucination_grader.md`: Grounding audit against context chunks.
- [ ] Implement nodes in `src/axiom/core/nodes/`.
- [ ] Assemble `src/axiom/core/graph.py` with conditional routing edges and loop ceiling guard ($\le 3$).
- [ ] Author unit tests in `tests/unit/test_graph.py`.

---

### Phase 4: Hybrid Ingestion & Retrieval Services `[PLANNED]`
- [ ] Implement markdown-preserving tabular document chunker.
- [ ] Build hybrid retrieval service (`src/axiom/services/vector_store.py`):
  - Qdrant dense vector search.
  - BM25 sparse keyword search.
  - Reciprocal Rank Fusion (RRF).
- [ ] Integrate cross-encoder re-ranking service (`src/axiom/services/reranker.py`).
- [ ] Integrate Tavily web search fallback (`src/axiom/services/web_search.py`).

---

### Phase 5: FastAPI Gateway & Real-Time SSE Streaming `[PLANNED]`
- [ ] Author FastAPI app in `src/axiom/api/main.py`.
- [ ] Implement SSE streaming endpoint `POST /api/v1/query` in `src/axiom/api/routes/chat.py`.
- [ ] Implement document upload endpoint `POST /api/v1/ingest` in `src/axiom/api/routes/ingest.py`.
- [ ] Implement health check & readiness probe in `src/axiom/api/routes/health.py`.
- [ ] Write integration test verifying SSE event order in `tests/integration/test_api_stream.py`.

---

### Phase 6: Golden Benchmark & Automated Evals `[PLANNED]`
- [ ] Curate 20+ multi-hop contract & 10-K test cases in `evals/golden_contracts.json`.
- [ ] Author automated evaluation runner in `evals/run_evals.py` using Ragas.
- [ ] Validate Faithfulness $\ge 0.95$, Answer Relevance $\ge 0.90$.

---

### Phase 7: Verification UI & Deployment `[PLANNED]`
- [ ] Build high-density enterprise dashboard using Axiom design tokens.
- [ ] Connect frontend to SSE streaming endpoint with real-time node state visualizer.
- [ ] Configure Redis / PostgreSQL state checkpointer.
- [ ] Author `deploy/docker-compose.yml`.
