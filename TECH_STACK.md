# Technology Stack & Architectural Justifications: Axiom & SCORE

> **Purpose**: Documents every technology selection in Axiom, why it was chosen over competing alternatives, and how it directly solves our production problems. This ensures complete institutional memory when developers or AI assistants work on the codebase.

---

## 1. Summary Tech Stack Matrix

| Layer | Selected Technology | Primary Alternatives Considered | Why We Selected It |
| :--- | :--- | :--- | :--- |
| **Language** | **Python 3.10+** | TypeScript, Rust, Go | The undisputed standard for AI/ML ecosystems, LangGraph, and embedding pipelines. |
| **Agent Orchestration** | **LangGraph** | LangChain LCEL, CrewAI, AutoGen | Deterministic cyclical state graphs, state checkpointing, and human-in-the-loop support. |
| **API Gateway** | **FastAPI** | Flask, Django, Express | Native async performance, Pydantic v2 schemas, auto OpenAPI docs, and native SSE streaming. |
| **Retrieval Strategy** | **Hybrid (Dense + Sparse BM25)** | Pure Dense Vector Search | Eliminates blindspots: Dense captures semantic intent; BM25 captures exact clause/ID numbers. |
| **Re-Ranking Layer** | **Cross-Encoder (Cohere / BGE)** | Raw Cosine Similarity | Full cross-attention between query and chunk tokens yields 30%+ higher precision. |
| **Vector Database** | **Qdrant** (with **Chroma** prototype) | Pinecone, Weaviate, Milvus | Rust-based performance, native sparse-dense payloads, air-gapped on-premise deployment option. |
| **LLM Tiering** | **Gemini Flash / GPT-4o-mini** (Grading) + **Gemini Pro / GPT-4o** (Generation) | Single monolithic model | Cuts token costs by 80% and reduces grading latency to ~200ms per chunk. |
| **Streaming Protocol**| **Server-Sent Events (SSE)** | WebSockets, Long Polling | Unidirectional HTTP/2 streaming, firewall friendly, lighter overhead than WebSockets. |
| **State Persistence** | **PostgreSQL / Redis Checkpointer** | In-Memory MemorySaver | Survives container restarts, supports conversational threads and audit replay. |
| **Evaluation Suite** | **Ragas & DeepEval** | Manual spot-checking | Quantitative, automated CI/CD scoring for Faithfulness, Relevance, and Precision. |
| **Observability** | **LangSmith / OpenTelemetry** | Raw logging | Full visualization of multi-step agent loops, latencies, and token costs. |

---

## 2. Deep Dive: Architectural Justifications

---

### 2.1 Agent Orchestration: LangGraph vs. Alternatives

#### Why LangGraph?
Standard RAG is a linear DAG (Directed Acyclic Graph): `Retriever -> Prompt -> LLM`. Production-grade RAG requires **cycles** and **stateful reflection**:
* If documents are irrelevant $\rightarrow$ rewrite query and retrieve again.
* If generated answer hallucinates $\rightarrow$ rewrite or regenerate.
* If 3 attempts fail $\rightarrow$ exit to fallback.

LangGraph provides:
1. **Explicit State Machines**: Every node accepts a strongly-typed `AgentState` and returns state mutations.
2. **First-Class Cyclical Graphs**: Loops are native language constructs, not awkward recursion hacks.
3. **Persistence Checkpointers**: Saves state at every node transition, enabling human-in-the-loop approval and crash recovery.

#### Why Not CrewAI or AutoGen?
* **CrewAI / AutoGen** are designed for conversational role-play between personas (e.g., "Researcher", "Writer"). In production search, this introduces massive, non-deterministic token chatter, unbudgeted latency, and unpredictable looping.
* **LangGraph** gives deterministic, predictable engineering control over every step of execution.

---

### 2.2 Retrieval Architecture: Hybrid Search (Dense + BM25) + Cross-Encoder

#### Why Pure Vector Search Fails in Production
Vector embeddings project text into continuous semantic space. While exceptional at understanding concepts (e.g., matching "automobile" with "car"), embeddings have a catastrophic blindspot: **exact alphanumeric tokens**.
* In enterprise contracts, queries often require exact match on clauses like: `"Section 4.1(b)"`, `"ISO-27001"`, or `"SOC2 Type II"`.
* Vector embeddings often score an irrelevant chunk with similar "legal vibe" higher than the chunk with the exact clause number.

#### How Axiom Solves It
1. **Dense Vector Search**: Captures thematic and conceptual context.
2. **Sparse BM25 Search**: Matches exact keywords, codes, section identifiers, and terminology.
3. **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse rankings into a unified candidate pool.
4. **Cross-Encoder Re-Ranking (Cohere / BGE)**: Passes the top candidates through a cross-encoder model that computes deep token-level cross-attention, filtering out false positives before they reach the LLM.

---

### 2.3 API Gateway & Streaming: FastAPI + Server-Sent Events (SSE)

#### Why SSE Over WebSockets?
* A self-correcting RAG loop takes between 2 to 6 seconds to execute. If a user stares at a blank loading spinner, they assume the system has crashed.
* We need to stream two streams of data:
  1. **Status Events**: `{"step": "grading", "chunks_kept": 3}`
  2. **Token Stream**: Incremental word tokens as the final answer generates.
* **WebSockets** require bidirectional stateful socket maintenance, complex ping/pong heartbeats, and tricky authentication handling across corporate firewalls and load balancers.
* **Server-Sent Events (SSE)** run over standard HTTP/2, are completely unidirectional (client requests, server pushes events), auto-reconnect natively, and require zero extra socket infrastructure.

---

### 2.4 Model Tiering: High-Reasoning vs. Fast-Grading Models

Running a multi-grader agent with top-tier models (e.g., GPT-4o or Claude 3.5 Sonnet) at every node would cause:
1. Multi-dollar API costs per query.
2. 10+ second latencies.

Axiom uses a **Two-Tier Architecture**:
* **Tier 1 (Fast & Structured)**: `gemini-1.5-flash` or `gpt-4o-mini`. Used for `Router`, `DocGrader`, `HallucinationGrader`, and `QueryRewriter`. Runs in ~200ms with strict JSON/Pydantic structured output.
* **Tier 2 (High-Reasoning & Synthesis)**: `gemini-1.5-pro`, `gpt-4o`, or `claude-3-5-sonnet`. Used exclusively for `AnswerGenerator` to synthesize intricate contractual nuances and format citations.

---

### 2.5 Automated Benchmarking: Ragas & DeepEval

#### Why Manual Eyeballing Fails
In AI development, prompt tweaks often produce the "balloon effect": fixing one edge case silently breaks three others.

#### Axiom's Automated CI/CD Metrics
Before any prompt or code change is merged, `evals/run_evals.py` runs against a golden dataset:
* **Faithfulness**: $\frac{\text{Number of claims in answer supported by context}}{\text{Total claims in answer}}$. Must be $\ge 0.95$.
* **Answer Relevance**: Semantic similarity between query and response. Must be $\ge 0.90$.
* **Context Precision**: Signal-to-noise ratio in retrieved context. Must be $\ge 0.85$.
