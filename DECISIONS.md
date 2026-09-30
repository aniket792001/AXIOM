# Architecture Decision Records (ADRs): Axiom & SCORE

> **Purpose**: Formal record of architectural decisions, their context, alternatives evaluated, and consequences. This prevents future contributors or AI coding assistants from regressing established designs.

---

## Index of Decisions

* [ADR-001: Adoption of LangGraph for Stateful Cyclical Orchestration](#adr-001-adoption-of-langgraph-for-stateful-cyclical-orchestration)
* [ADR-002: Hybrid Retrieval (Dense Vectors + Sparse BM25) with Cross-Encoder Re-Ranking](#adr-002-hybrid-retrieval-dense-vectors--sparse-bm25-with-cross-encoder-re-ranking)
* [ADR-003: Server-Sent Events (SSE) over WebSockets for Real-Time Streaming](#adr-003-server-sent-events-sse-over-websockets-for-real-time-streaming)
* [ADR-004: Epistemic Humility as Core Prompt Engineering Philosophy](#adr-004-epistemic-humility-as-core-prompt-engineering-philosophy)
* [ADR-005: Two-Tier LLM Architecture for Cost & Latency Optimization](#adr-005-two-tier-llm-architecture-for-cost--latency-optimization)
* [ADR-006: Hard Loop Ceiling of Maximum 3 Retries](#adr-006-hard-loop-ceiling-of-maximum-3-retries)

---

### ADR-001: Adoption of LangGraph for Stateful Cyclical Orchestration
* **Status**: Accepted
* **Context**: Traditional RAG architectures rely on linear, unidirectional pipelines (`Retriever -> Prompt -> LLM`). When retrieved context is noisy or irrelevant, a linear pipeline has no mechanism to recover.
* **Decision**: Use **LangGraph** to model the RAG process as a cyclic state machine with conditional routing edges and checkpointing.
* **Alternatives Considered**:
  * *LangChain LCEL*: Great for linear chains, but cumbersome and unnatural for stateful loops with retry counters.
  * *CrewAI / AutoGen*: Designed for conversational persona role-play; introduces non-deterministic token chatter and excessive latency.
* **Consequences**:
  * *Positive*: Explicit typed state (`AgentState`), deterministic graph loops, native state persistence for human-in-the-loop.
  * *Trade-off*: Slightly steeper learning curve than simple linear chains.

---

### ADR-002: Hybrid Retrieval (Dense Vectors + Sparse BM25) with Cross-Encoder Re-Ranking
* **Status**: Accepted
* **Context**: Pure dense vector search fails on precise alphanumeric symbols, section numbers (e.g., "Section 4.1(b)"), and legal clause cross-references.
* **Decision**: Implement a two-stage retrieval pipeline:
  1. Retrieve top-25 candidates using **Hybrid Search** (Dense embeddings via Qdrant/Chroma + Sparse BM25 keyword matching merged with Reciprocal Rank Fusion).
  2. Re-rank top-25 down to top-5 using a **Cross-Encoder Re-ranker** (Cohere Rerank / BGE-Reranker-Large).
* **Alternatives Considered**:
  * *Pure Dense Vector Search*: Failed on exact contractual clauses and numerical IDs.
  * *Raw Cosine Distance without Re-ranking*: Passed too much irrelevant noise to the LLM grader.
* **Consequences**:
  * *Positive*: Order-of-magnitude increase in precision on exact contract terminology.
  * *Trade-off*: Adds ~100-150ms latency for the re-ranking step.

---

### ADR-003: Server-Sent Events (SSE) over WebSockets for Real-Time Streaming
* **Status**: Accepted
* **Context**: Multi-step agent reflection loops take 2 to 6 seconds. Users require continuous visual feedback showing both the agent's internal progress (`status` events) and the final response (`token` stream).
* **Decision**: Use **Server-Sent Events (SSE)** via FastAPI and `sse-starlette` over standard HTTP/2.
* **Alternatives Considered**:
  * *WebSockets*: Bidirectional stateful TCP sockets introduce proxy, firewall, load balancer, and authentication complexities where only server-to-client streaming is needed.
  * *Long Polling*: High HTTP overhead and clunky for streaming tokens.
* **Consequences**:
  * *Positive*: Lightweight, unidirectional, firewall-friendly, native browser `EventSource` support.
  * *Trade-off*: Strictly unidirectional (client cannot send messages back down the same stream; new requests use standard POST endpoints).

---

### ADR-004: Epistemic Humility as Core Prompt Engineering Philosophy
* **Status**: Accepted
* **Context**: In consumer AI, assistants are trained to be "helpful" by guessing or extrapolating when information is missing. In enterprise legal and financial contexts, this leads to catastrophic hallucinations.
* **Decision**: Mandate **Epistemic Humility** across all prompts. The system must never guess, never extrapolate, and explicitly state what is missing if verified facts cannot be found.
* **Alternatives Considered**:
  * *Permissive Generation*: Allowing the model to use internal training weights when retrieval is weak. (Rejected: Violates enterprise zero-hallucination requirement).
* **Consequences**:
  * *Positive*: Guaranteed auditability and trust; users can rely 100% on citations.
  * *Trade-off*: The model will refuse to answer questions if documents lack explicit evidence.

---

### ADR-005: Two-Tier LLM Architecture for Cost & Latency Optimization
* **Status**: Accepted
* **Context**: Running top-tier reasoning models (GPT-4o, Claude 3.5 Sonnet) at every node (Router, Doc Grader, Hallucination Grader, Relevance Grader, Generator) causes $0.15+ costs per query and 10+ second latencies.
* **Decision**: Adopt a dual-tier model hierarchy:
  * **Tier 1 (Fast & Structured)**: `gemini-1.5-flash` or `gpt-4o-mini` for routing, grading, and query rewriting (~200ms latency, 80% lower cost).
  * **Tier 2 (High-Reasoning)**: `gemini-1.5-pro`, `gpt-4o`, or `claude-3-5-sonnet` exclusively for final answer synthesis and citation formatting.
* **Consequences**:
  * *Positive*: Total query latency stays within 2.5–4.5s; operational cost reduced by >75%.
  * *Trade-off*: Requires maintaining configurations for two model tiers.

---

### ADR-006: Hard Loop Ceiling of Maximum 3 Retries
* **Status**: Accepted
* **Context**: Cyclical agent graphs risk infinite loops if retrieval repeatedly fails or query rewriting produces unanswerable variations.
* **Decision**: Enforce a strict `loop_count <= 3` guard in `AgentState`. If attempt 3 fails, the graph must route to `FallbackHandler`.
* **Consequences**:
  * *Positive*: Predictable maximum latency and hard budget ceiling on API token costs.
  * *Trade-off*: Some edge-case queries that might have succeeded on attempt 4 will gracefully fail.
