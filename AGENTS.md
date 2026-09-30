# Universal AI Agent Guide (AGENTS.md)

> **Audience**: Autonomous AI agents, coding assistants (Antigravity, Claude Code, Cursor, Windsurf, GitHub Copilot, Aider, etc.), and human engineers.  
> **Directive**: Read this file first before inspecting or modifying any code in this repository.

---

## 1. Project Identity & Purpose
* **Project**: **Axiom**
* **Core Engine**: **SCORE** (*Self-COrrecting Reasoning Engine*)
* **Repository Mission**: Enterprise-grade self-correcting RAG platform that eliminates hallucinations and solves multi-hop contractual/financial contradictions.
* **Core Philosophy**: **Epistemic Humility** (Never bluff, never extrapolate beyond context, cite every claim).

---

## 2. Mandatory Rules & Invariants for AI Coding Assistants

Whenever you are asked to generate code, write tests, or modify prompts:

### Invariant 1: Never Bypass the Grading Loops
* Every retrieved document **must** pass through `DocGrader` before being passed to `AnswerGenerator`.
* Every generated answer **must** pass through `HallucinationGrader` before being streamed to the user.
* Do not "simplify" the graph by connecting the retriever directly to the generator.

### Invariant 2: Strictly Typed State
* All graph state transformations must use the strongly typed `AgentState` schema defined in `src/axiom/core/state.py`.
* Never pass unvalidated dictionaries or untyped objects between nodes.

### Invariant 3: Hard Loop Ceiling
* The reflection/retry loop must strictly respect `loop_count <= 3`.
* If 3 loops expire without finding sufficient context, the engine must route to `FallbackHandler`. Never allow an infinite loop.

### Invariant 4: Decoupled Prompts
* Do not embed prompt strings directly inside Python node files.
* All prompt templates must live in `src/axiom/core/prompts/` as clean Markdown/Jinja files.

### Invariant 5: Preserve Markdown Tables
* Document chunking and parsing must never strip Markdown tables or separate financial metrics from explanatory footnotes.

---

## 3. Technology Stack Reference

If you are asked to install packages or refactor code, stick strictly to these chosen technologies:
* **Language**: Python 3.10+
* **Orchestration**: `langgraph` (stateful cyclical graph, not linear chains)
* **API Gateway**: `fastapi` with `sse-starlette` (Server-Sent Events)
* **Configuration**: `pydantic-settings` v2
* **Vector Store**: `qdrant-client` (with `chromadb` prototype fallback)
* **Sparse Keyword Search**: `rank-bm25`
* **Re-Ranking**: `cohere` or `sentence-transformers` cross-encoder
* **Evaluation**: `ragas` and `pytest`
* **Linting / Formatting**: `ruff`

*(See [TECH_STACK.md](TECH_STACK.md) and [DECISIONS.md](DECISIONS.md) for detailed justifications).*

---

## 4. Common Agent Workflows & Commands

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run automated Ragas evaluation suite
python evals/run_evals.py

# Format and lint code
ruff format .
ruff check .

# Type checking
mypy src/

# Run FastAPI development server with hot-reload
uvicorn src.axiom.api.main:app --reload --port 8000
```

---

## 5. File Orientation Map

| What you need to know | Where to look |
| :--- | :--- |
| **High-level overview & brand** | [README.md](README.md) |
| **Brand & Architecture Foundation** | [AXIOM_FOUNDATION.md](AXIOM_FOUNDATION.md) |
| **Full technical specification** | [docs/brand_and_architecture_spec.md](docs/brand_and_architecture_spec.md) |
| **1M Customer Scaling Architecture** | [SCALING_ARCHITECTURE.md](SCALING_ARCHITECTURE.md) |
| **Domain context & failure modes** | [CONTEXT.md](CONTEXT.md) |
| **Why we chose this tech stack** | [TECH_STACK.md](TECH_STACK.md) |
| **Architectural Decision Records** | [DECISIONS.md](DECISIONS.md) |
| **Current project status & tasks** | [TODO.md](TODO.md) |
| **Long-term engineering roadmap** | [ROADMAP.md](ROADMAP.md) |
| **Coding & PR standards** | [CONTRIBUTING.md](CONTRIBUTING.md) |
