# ⚡ Axiom & SCORE Engine: Complete System Visual Flow

> Visual reference guide for the **Axiom** architecture, execution lifecycle, dual self-correction loops, and multi-tenant hybrid retrieval pipeline.

---

## 1. High-Level System Architecture Topology

The entire system is composed of four decoupled operational tiers: **Client Layer**, **API Gateway & Streaming Tier**, **SCORE Cyclical State Machine**, and **Multi-Tenant Data & Model Tier**.

```mermaid
flowchart TB
    subgraph ClientLayer["1. Client & Presentation Layer"]
        UI["Axiom Verification Dashboard<br/>(Vanilla JS / Tailwind-style Dark Mode)"]
        SSEClient["SSE Event Listener<br/>(Real-Time State Visualizer)"]
        CitationDrawer["Citation & Audit Drawer<br/>(Direct Document Verification)"]
        UI --- SSEClient
        UI --- CitationDrawer
    end

    subgraph APITier["2. API Gateway Tier (FastAPI + Starlette)"]
        ChatRoute["Chat & Query Endpoint<br/>(/api/v1/query)"]
        StreamRoute["SSE Streaming Engine<br/>(/api/v1/query/stream)"]
        HealthRoute["Readiness & Liveness<br/>(/api/v1/health)"]
    end

    subgraph CoreEngine["3. SCORE Engine (LangGraph State Machine)"]
        State["AgentState<br/>(Strictly-Typed Context Object)"]
        Graph["Cyclical Multi-Agent Graph<br/>(Router, Retriever, Graders, Rewriter, Generator)"]
    end

    subgraph DataServices["4. Retrieval, Storage & Model Services"]
        Qdrant["Dense Vector Store<br/>(Qdrant Cloud / Local Memory)"]
        BM25["Sparse Keyword Index<br/>(BM25Plus with Tenant Isolation)"]
        Reranker["Cross-Encoder Re-ranker<br/>(Semantic Precision Filtering)"]
        LLM["Inference Models<br/>(Gemini 2.5 / OpenAI / Local Fallback)"]
    end

    ClientLayer ==>|HTTP POST Query| APITier
    APITier ==>|Initializes State| CoreEngine
    CoreEngine <==>|Hybrid Search & Reranking| DataServices
    CoreEngine <==>|Structured Generation & Grading| LLM
    StreamRoute -.->|Async SSE Chunks & Trace Events| SSEClient
```

---

## 2. The 9-Node SCORE State Machine (Detailed Execution Flow)

At the heart of Axiom is the cyclical state machine implemented in [`src/axiom/core/graph.py`](file:///e:/AXIOM/src/axiom/core/graph.py). It continuously audits both retrieved inputs and generated outputs:

```mermaid
flowchart TD
    %% Entry Point
    Start([User Ingestion / Query]) --> N_Router["1. Router Node<br/>(Intent Classification)"]

    %% Routing Decisions
    N_Router -- "route == 'web_search'" --> N_Web["2a. Web Search Node<br/>(Tavily API)"]
    N_Router -- "route == 'vector_store'" --> N_Retriever["2b. Retriever Node<br/>(Hybrid Qdrant + BM25)"]
    N_Router -- "route == 'direct'" --> N_Generator["5. Generator Node<br/>(Direct Synthesis)"]

    %% Re-Ranking to Document Grading
    N_Web --> N_Grader["3. Document Grader Node<br/>(Relevance Filtering)"]
    N_Retriever --> N_Grader

    %% Conditional Edge: decide_after_grading
    N_Grader --> Cond_Grade{"Any Graded Docs Retained?"}

    Cond_Grade -- "Yes (Docs >= 1)" --> N_Generator

    %% Self-Correction Loop 1: Query Expansion
    Cond_Grade -- "No (Empty Docs)" --> Cond_Loop1{"loop_count < 3?"}
    Cond_Loop1 -- "Yes (Retry permitted)" --> N_Rewriter["4. Query Rewriter Node<br/>(Expands terms, adds amendments)"]
    N_Rewriter -->|Loop count += 1| N_Retriever
    Cond_Loop1 -- "No (Exceeded limit)" --> N_Fallback["6. Fallback Handler<br/>(Epistemic Humility Refusal)"]

    %% Generation to Hallucination Grading
    N_Generator --> N_Hallucination["7. Hallucination Grader Node<br/>(Grounding & Fact Verification)"]

    %% Conditional Edge: decide_after_hallucination
    N_Hallucination --> Cond_Hallucination{"Status == 'grounded'?"}

    Cond_Hallucination -- "Yes (100% Grounded)" --> EndSuccess([Final Verified Answer + Citations])
    Cond_Hallucination -- "No (Hallucinated)" --> Cond_Loop2{"loop_count < 3?"}
    Cond_Loop2 -- "Yes (Re-attempt generation)" --> N_Generator
    Cond_Loop2 -- "No (Exceeded limit)" --> N_Fallback

    N_Fallback --> EndRefusal([Transparent Diagnostic Refusal])

    %% Styling
    classDef verified fill:#10B981,stroke:#047857,stroke-width:2px,color:#ffffff;
    classDef warning fill:#F59E0B,stroke:#B45309,stroke-width:2px,color:#ffffff;
    classDef rejected fill:#EF4444,stroke:#B91C1C,stroke-width:2px,color:#ffffff;
    classDef nodeStyle fill:#112240,stroke:#233554,stroke-width:2px,color:#E2E8F0;

    class EndSuccess verified;
    class N_Rewriter,Cond_Loop1,Cond_Loop2 warning;
    class N_Fallback,EndRefusal rejected;
    class N_Router,N_Web,N_Retriever,N_Grader,N_Generator,N_Hallucination nodeStyle;
```

---

## 3. End-to-End Query Lifecycle (Sequence Diagram)

This diagram details the request-response cycle and async Server-Sent Event (SSE) updates as a query moves across components:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Frontend UI
    participant Gateway as FastAPI Router (/api/v1/query/stream)
    participant Graph as LangGraph Orchestrator
    participant Store as Hybrid Store (Qdrant + BM25)
    participant Grader as Relevance Grader
    participant Generator as Grounded Generator
    participant Audit as Hallucination Grader

    User->>Gateway: POST /api/v1/query/stream (query, tenant_id)
    Gateway-->>User: SSE Event: status (initialized)

    Gateway->>Graph: invoke(initial_state)

    %% Step 1: Router
    Graph->>Graph: Execute router_node
    Gateway-->>User: SSE Event: status (node: "router")

    %% Step 2: Retrieval
    Graph->>Store: hybrid_search(tenant_id, query)
    Store-->>Graph: Top-10 Dense + Sparse Chunks
    Graph->>Store: rerank(top_k=5)
    Store-->>Graph: Top-5 Semantically Filtered Chunks
    Gateway-->>User: SSE Event: status (node: "retriever")

    %% Step 3: Grading
    Graph->>Grader: Evaluate relevance of each chunk
    Grader-->>Graph: graded_documents (filtered noise)
    Gateway-->>User: SSE Event: status (node: "grader")

    alt Context Insufficient (Docs == 0 & loop < 3)
        Graph->>Graph: rewriter_node (expand search query)
        Gateway-->>User: SSE Event: status (node: "rewriter", loop_count: 1)
        Graph->>Store: re-retrieve with expanded query
    end

    %% Step 4: Generation
    Graph->>Generator: Synthesize answer with bracketed citations [doc_id]
    Generator-->>Graph: generation_text + citations
    Gateway-->>User: SSE Event: status (node: "generator")

    %% Step 5: Hallucination Audit
    Graph->>Audit: Compare generation against graded_documents
    alt Zero Hallucinations Detected
        Audit-->>Graph: hallucination_status = "grounded"
        Gateway-->>User: SSE Event: answer (generation + citations)
    else Hallucination Detected (loop < 3)
        Audit-->>Graph: hallucination_status = "hallucinated"
        Graph->>Generator: Re-generate strictly without invented facts
    end

    %% Completion
    Gateway-->>User: SSE Event: done (status: "completed")
```

---

## 4. Multi-Tenant Hybrid Retrieval Pipeline

The retrieval tier guarantees tenant data isolation while combining vector similarity with exact term matching:

```mermaid
flowchart LR
    subgraph QueryIn["Query Input"]
        Q["User Query / Rewritten Query"]
        TID["Tenant ID Token"]
    end

    subgraph DenseBranch["1. Dense Vector Branch"]
        Embed["Embedding Model<br/>(text-embedding-004)"]
        QdrantColl["Qdrant Vector Store<br/>(Filtered by tenant_id)"]
        DenseScores["Dense Top-K Candidates<br/>(Cosine Similarity)"]
        Embed --> QdrantColl --> DenseScores
    end

    subgraph SparseBranch["2. Sparse Keyword Branch"]
        Tokenizer["Alphanumeric Tokenizer<br/>(Preserves section/clause IDs)"]
        BM25Index["BM25Plus Corpus Index<br/>(Partitioned by tenant_id)"]
        SparseScores["Sparse Top-K Candidates<br/>(Term Frequency Matches)"]
        Tokenizer --> BM25Index --> SparseScores
    end

    subgraph Fusion["3. Reciprocal Rank Fusion (RRF)"]
        RRFFormula["RRF Score = Sum( 1 / (60 + Rank) )"]
        FusedPool["Fused Candidate Pool (Top 10)"]
        DenseScores --> RRFFormula
        SparseScores --> RRFFormula
        RRFFormula --> FusedPool
    end

    subgraph ReRanking["4. High-Precision Re-Ranker"]
        CrossEncoder["Cross-Encoder / Cohere Reranker<br/>(Deep Query-Document Attention)"]
        TopChunks["Top-5 Clean Chunks<br/>(Passed to Grader Node)"]
        FusedPool --> CrossEncoder --> TopChunks
    end

    Q --> Embed
    Q --> Tokenizer
    TID --> QdrantColl
    TID --> BM25Index
```

---

## 5. Visualizing How Axiom Solves the 4 Enterprise RAG Failures

```
+----------------------------------------------------------------------------------------------------+
| 1. THE AMENDMENT TRAP                                                                              |
| Standard RAG: Finds 2022 MSA ($1M liability cap) -> Outputs legally void terms.                   |
| Axiom SCORE:  Doc Grader flags missing active terms -> Query Rewriter searches for 'Addendum'     |
|               -> Retrieves 2024 Addendum No. 3 ($2.5M cap) -> Verifies superseding clause.         |
+----------------------------------------------------------------------------------------------------+
| 2. THE MULTI-HOP DISCONNECT                                                                        |
| Standard RAG: Section 2.4 says 'governed by Appendix IV' -> Answers without seeing Appendix IV.    |
| Axiom SCORE:  Doc Grader checks clause completeness -> Rewriter retrieves Appendix IV on page 88   |
|               -> Synthesizes mandatory 3-year cliff vesting terms.                                 |
+----------------------------------------------------------------------------------------------------+
| 3. TABULAR FOOTNOTE DISTORTION                                                                     |
| Standard RAG: Reads Financial Table ($450M operating income) -> Misses restructuring note.         |
| Axiom SCORE:  Table Preserving Parser connects Markdown table with Footnote 14b                    |
|               -> Explains $120M one-off divestiture; reveals $330M recurring operational income.   |
+----------------------------------------------------------------------------------------------------+
| 4. THE SILENT BLUFF (Zero-Hallucination)                                                           |
| Standard RAG: Query asks for unsupported cloud region -> LLM invents plausible fake SLA numbers.   |
| Axiom SCORE:  Context missing verified SLA -> Loop counter exhausts -> Fallback Handler triggers   |
|               -> Returns honest refusal with exact search audit trail. Never bluffs.               |
+----------------------------------------------------------------------------------------------------+
```

---

## 6. AgentState Transformation Across Nodes

| Node Name | Inputs Read from State | Outputs Written / Appended to State |
| :--- | :--- | :--- |
| [`router`](file:///e:/AXIOM/src/axiom/core/nodes/router.py) | `query` | `route` ("vector_store" \| "web_search" \| "direct"), `reasoning_trace` |
| [`retriever`](file:///e:/AXIOM/src/axiom/core/nodes/retriever.py) | `query`, `rewritten_query`, `route`, `tenant_id` | `documents` (List[DocumentChunk]), `reasoning_trace` |
| [`grader`](file:///e:/AXIOM/src/axiom/core/nodes/grader.py) | `query`, `documents` | `graded_documents` (retained relevant chunks), `reasoning_trace` |
| [`rewriter`](file:///e:/AXIOM/src/axiom/core/nodes/rewriter.py) | `query`, `loop_count`, `rewritten_query` | `rewritten_query`, `loop_count` (+1), `reasoning_trace` |
| [`generator`](file:///e:/AXIOM/src/axiom/core/nodes/generator.py) | `query`, `graded_documents` | `generation` (answer text), `citations` (List[Citation]), `reasoning_trace` |
| [`hallucination_grader`](file:///e:/AXIOM/src/axiom/core/nodes/hallucination_grader.py) | `generation`, `graded_documents` | `hallucination_status` ("grounded" \| "hallucinated"), `reasoning_trace` |
| [`fallback`](file:///e:/AXIOM/src/axiom/core/nodes/fallback.py) | `query`, `loop_count`, `rewritten_query` | `generation` (diagnostic refusal), `fallback_reason`, `hallucination_status` = "grounded", `reasoning_trace` |
