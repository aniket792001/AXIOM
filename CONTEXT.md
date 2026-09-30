# Project Context & Domain Manifesto: Axiom & SCORE

> **Purpose of this document**: Provides comprehensive domain background, the real-world problem statement, and core architectural invariants for developers, stakeholders, and AI pair-programming agents.

---

## 1. The Crisis of Enterprise RAG (2024–2026)

In 2023, the software world believed Retrieval-Augmented Generation (RAG) had "solved" enterprise search. Developers could write 25 lines of LangChain code, point embeddings at a folder of PDFs, and produce an impressive demo in an afternoon.

By 2025, enterprise IT departments had stalled or killed over 70% of RAG pilot projects. Why?
* **The 80% Paradox**: In consumer chatbots, 80% accuracy feels like magic. In high-stakes enterprise workflows (corporate legal, financial audits, medical protocol, critical infrastructure), **80% accuracy is catastrophic**.
* **The Silent Hallucination Threat**: When a human doesn't know an answer, they say "I don't know." When standard RAG retrieves incomplete or conflicting context, the LLM bridges the gap by synthesizing a confident, plausible-sounding lie.
* **The Static Pipeline Fallacy**: Traditional RAG is a one-way pipeline: `Query -> Embed -> Cosine Top-K -> Prompt -> LLM Output`. It has no feedback loops, no self-criticism, and no mechanism to verify whether the retrieved text actually supports the generated claims.

**Axiom was created to replace static RAG pipelines with self-correcting cognitive loops.**

---

## 2. The Spearhead Domain: High-Stakes Financial & Regulatory Audits

While Axiom's underlying **SCORE Engine** is domain-agnostic, we anchor our engineering and benchmarking around the most demanding domain: **Financial Due Diligence & Regulatory Contract Auditing**.

### Why This Domain?
1. **Catastrophic Cost of Failure**: A missed debt covenant or misinterpreted liability clause can cost millions in penalties or litigation.
2. **Extreme Document Complexity**: SEC 10-K filings, loan agreements, and Master Service Agreements (MSAs) are filled with cross-references, numerical tables, and superseding amendments.
3. **Publicly Accessible Golden Data**: Public SEC filings (e.g., Apple, Tesla, Alphabet 10-Ks) and open corporate contract datasets allow us to construct rigorous, reproducible automated benchmarks without proprietary NDAs.

---

## 3. The 4 Real-World Failure Modes Axiom Eliminates

```
[Traditional RAG Failure Matrix]

1. The "Amendment" Trap:
   • Document A (2022 Master Agreement): Liability cap is $1,000,000.
   • Document B (2024 Addendum Section 3.2): Amends liability cap to $2,500,000 for enterprise tiers.
   • Standard RAG: Vector search matches the longer 2022 text. Outputs $1,000,000. 
   • Axiom Solution: Multi-hop query expansion flags the superseding addendum and verifies temporal precedence.

2. The "Multi-Hop Disconnect":
   • Document A: "All employees in Group C are subject to Appendix IV vesting."
   • Document B (Appendix IV, 80 pages away): "Group C vesting requires 3-year cliff."
   • Standard RAG: Retrieves Document A only. Hallucinates standard 1-year vesting.
   • Axiom Solution: Document Grader flags missing definitions and recursively queries for Appendix IV.

3. The "Table & Footnote Distortion":
   • Income Statement: "Operating Income: $450 Million."
   • Footnote 14b: "Includes $120 Million one-off gain from subsidiary divestiture."
   • Standard RAG: Scrambles table markdown; ignores the footnote; misstates operational run-rate.
   • Axiom Solution: Markdown-preserving tabular ingestion + numerical verification guardrail.

4. The "Silent Bluff":
   • User Query: "What is our company's disaster recovery SLA for AWS us-west-1?"
   • Context: Internal docs only mention Azure and GCP.
   • Standard RAG: Generates a plausible 99.99% AWS SLA out of training weights.
   • Axiom Solution: Dual hallucination and relevance graders detect zero factual grounding and trigger a clean, diagnostic refusal.
```

---

## 4. The Golden Benchmark Scenario (The Acid Test)

Every iteration of Axiom's SCORE engine is tested against this canonical scenario:

```
================================================================================
INPUT DATASET:
- File 1: "Enterprise_SaaS_MSA_2022.pdf" (Initial agreement, 45 pages)
- File 2: "Enterprise_SaaS_Addendum_2024.pdf" (Addendum, 3 pages)

USER QUERY:
"What is the liability cap and termination notice period for Tier 2 enterprise customers?"

EXPECTED AXIOM TRACE:
1. Router classifies intent -> Internal Vector Store.
2. HybridRetriever retrieves candidate chunks from both files.
3. CrossEncoderReranker prioritizes high-relevance clauses.
4. DocGrader evaluates candidate chunks:
   - Chunk #1 (2022 MSA): "Liability is capped at $1,000,000. Notice is 30 days." -> Relevance: YES (Initial)
   - Chunk #2 (2024 Addendum): "Section 4.1 amended: Tier 2 liability cap increased to $2,500,000; notice extended to 60 days." -> Relevance: YES (Superseding)
5. AnswerGenerator synthesizes grounded answer:
   "Under the 2024 Addendum (Section 4.1), which supersedes the 2022 MSA, the liability cap for Tier 2 enterprise customers is $2,500,000 and the termination notice period is 60 days."
6. HallucinationGrader verifies:
   - Claim 1 ($2.5M) -> Verified against Chunk #2.
   - Claim 2 (60 days) -> Verified against Chunk #2.
   - Claim 3 (supersedes 2022 MSA) -> Verified against Chunk #2 Section 4.1.
   -> Hallucination Score: 0.0 (100% Grounded).
7. Final Output emitted via SSE stream with exact chunk citations.
================================================================================
```

---

## 5. Invariants for AI & Human Developers

When contributing code, modifying prompts, or refactoring the graph, you **must adhere to these invariants**:

1. **State Immutability & Typing**: Always use the typed `AgentState` schema. Never pass loose dictionaries between nodes.
2. **Loop Ceiling**: The `loop_count` guard must strictly enforce a maximum of 3 retries to prevent infinite token consumption or runaway latency.
3. **Decoupled Prompts**: Keep prompts in `src/axiom/core/prompts/`. Never hardcode prompts inside Python node functions.
4. **Epistemic Humility Over Helpfulness**: If the retrieved documents do not contain the answer, the engine **must admit it cannot find the answer**. It is strictly forbidden to instruct the LLM to "be helpful and extrapolate."
5. **Every Claim Must Have an ID**: The generator must output citations in the format `[doc_id:chunk_id]`.
