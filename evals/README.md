# Axiom Golden Evaluation Benchmark

> Automated CI/CD benchmarking framework designed to evaluate factual grounding, amendment prioritization, and silent bluff prevention across complex enterprise contracts.

---

## 🎯 Benchmark Categories

The benchmark dataset in `golden_contracts.json` evaluates four critical production failure modes:

| Test ID | Benchmark Category | Description | Success Metric |
| :--- | :--- | :--- | :--- |
| `eval_001` | **Amendment Tracking** | Catches superseding addendums (e.g. 2024 addendum amending a 2022 liability cap). | Highest-ranking citations reference superseding addendum; zero hallucinated terms. |
| `eval_002` | **Multi-Hop Reasoning** | Cross-references clauses pointing to appendices located 50+ pages away. | Correct appendix terms synthesized without guessing. |
| `eval_003` | **Tabular Audit** | Reconciles financial tables with clarifying footnote disclosures. | Correct net operational figure cited without scrambling table markdown. |
| `eval_004` | **Epistemic Humility** | Evaluates response when verified evidence does not exist in context. | Emits transparent refusal explaining missing facts rather than inventing a hallucinated number. |

---

## 🚀 Running the Benchmark

Execute the automated benchmark runner:

```bash
# Set Python path to src
export PYTHONPATH="src"   # On Windows: $env:PYTHONPATH="src"

# Run evaluation suite
python evals/run_evals.py
```

Expected Output:
```
================================================================================
AXIOM & SCORE ENGINE: GOLDEN CONTRACT EVALUATION BENCHMARK
================================================================================

Test Case                                  | Verdict  | Grounded | Coverage | Latency  
--------------------------------------------------------------------------------
The Amendment Trap (Superseding Liability  | PASSED   | YES      | 50.0%    | 8.7ms    
The Multi-Hop Disconnect (Separated Append | PASSED   | YES      | 100.0%   | 5.2ms    
Table and Footnote Distortion (Financial O | PASSED   | YES      | 100.0%   | 4.6ms    
Silent Bluff Prevention (Epistemic Humilit | PASSED   | YES      | 100.0%   | 4.1ms    
================================================================================
BENCHMARK SUMMARY: 4/4 Passed (100.0%) | Avg Latency: 5.6ms
================================================================================
```
