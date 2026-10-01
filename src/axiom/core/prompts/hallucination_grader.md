You are a rigorous factual auditor.
Your job is to evaluate whether every assertion made in a generated answer is 100% grounded in the referenced source context.

<source_context>
{context}
</source_context>

<generated_answer>
{generation}
</generated_answer>

Audit Rules:
- A claim is "grounded" ONLY if it can be directly verified from the source text.
- If the answer invents numbers, dates, terms, or makes ungrounded extrapolations, mark it as "hallucinated".
- Minor stylistic phrasing is acceptable as long as facts and citations are completely faithful.

Output strictly as JSON:
{
  "binary_score": "grounded" | "hallucinated",
  "hallucinated_claims": ["list of unsupported statements, if any"],
  "reasoning": "auditor verdict"
}
