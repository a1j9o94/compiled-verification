# E-C1 Findings: LLM Judge Variance

**Status:** Not Started
**Last Updated:** —

## Results Summary

*(populate after running experiments)*

| Condition | Syntactic Agreement | Numeric Agreement | Semantic Agreement |
|-----------|--------------------|--------------------|-------------------|
| A: Baseline | — | — | — |
| B: Chain-of-Thought | — | — | — |
| C: Structured Output | — | — | — |
| D: Few-Shot | — | — | — |
| E: Specific Rubric | — | — | — |

## Hypothesis Status

- [ ] Claim 1 supported: semantic variance > 30pp higher than syntactic
- [ ] Prompting improvement < 20pp from A → E on semantic criteria
- [ ] ANOVA p < 0.01 for syntactic vs semantic variance difference
- [ ] Intra-judge self-consistency < 85% for semantic criteria

## Key Numbers for Article

*(fill in after analysis)*

> "Across [N] financial model evaluations, 4 LLM judges agreed on all semantic
> criteria only [X]% of the time. Chain-of-thought prompting raised this to [Y]%.
> The ceiling is structural, not prompting."

## Falsification Check

- [ ] Did semantic agreement exceed 90% in any condition? → If yes, hypothesis falsified.
- [ ] Did tool calling eliminate semantic variance (E-C2)? → If yes, Tier 2 is sufficient.
