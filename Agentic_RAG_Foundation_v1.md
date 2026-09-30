# Agentic RAG: Project Foundation

## 1. Brand Identity & Name
- **Proposed Names**: 
  - **AxiomRAG**: Implies foundational truth and precision.
  - **SCORE (Self-COrrecting RAG Engine)**: Highlights the core functionality.
  - **CogniRAG**: Emphasizes the cognitive, agentic loops.
- **Tagline**: "Beyond Retrieval. Towards Reasoning."
- **Brand Identity**: Professional, reliable, and intelligent. 
- **Tone**: Authoritative yet accessible. The system should feel like a diligent researcher who double-checks their work.

## 2. Why This Exists (The Problem)
Standard Retrieval-Augmented Generation (RAG) is flawed. While it provides a knowledge base for LLMs, tech teams frequently encounter its limits:
- **Bad Retrieval**: Fetching irrelevant or noisy chunks of text.
- **Hallucinations**: The LLM inventing facts when the retrieved context is poor or missing.
- **Static Pipelines**: Traditional RAG blindly passes retrieved context to the LLM without evaluating its quality or relevance.

Agentic RAG exists to break through this ceiling by transforming a static pipeline into an active, thinking agent that actively fixes these issues.

## 3. How and Where It Solves the Problem
Agentic RAG solves these issues by introducing three foundational agent loops:

1. **Routing**: Dynamically deciding whether to query the vector storage, search the live web, or request human clarification based on the user's query intent.
2. **Evaluation/Grading**: Using smaller, fast models (or structured outputs) to score retrieved chunks for relevance. Irrelevant chunks are discarded before passing to the generation phase.
3. **Self-Correction & Fallback**: Detecting hallucinations or incomplete context during generation, and looping back to rewrite the query or retrieve again.

**Where it applies**: 
- High-stakes enterprise search
- Automated customer support bots
- Technical documentation assistants
- Legal and medical document analysis (where hallucinations are unacceptable)

## 4. Proper Documentation Structure
To ensure the project remains manageable, measurable, and straightforward to trace, we will maintain the following documentation structure:
- `README.md`: High-level overview, quick start guide, and system architecture diagram.
- `docs/architecture.md`: Detailed breakdown of the agent loops (Routing, Grading, Correction).
- `docs/guidelines.md`: Coding standards, prompt engineering best practices, and contribution rules.
- `docs/evaluation.md`: Benchmarking and tracing guides using tools like LangSmith or Phoenix.

## 5. Rules & Guidelines
- **Rule 1: Never Trust Retrieval Blindly**: Every retrieved chunk must pass a relevance grader before generation.
- **Rule 2: Trace Everything**: All agent loops (routing, grading, generating) must be observable and traceable. Manageable scope means high visibility.
- **Rule 3: Graceful Fallbacks**: If the system cannot find an accurate answer after maximum retries, it must explicitly state its inability or route to a human, rather than hallucinate.
- **Rule 4: Modularity**: Prompts, LLM models, and Vector Stores must be decoupled and easily interchangeable.
