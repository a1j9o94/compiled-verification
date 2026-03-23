# E-C1 Findings: LLM Judge Variance — Surprising Results

**Status:** Complete
**Last Updated:** 2026-03-22
**Judges:** GPT-4o (gpt-4o-2024-11-20), Claude Sonnet 4.6 (claude-sonnet-4-20250514)
**Note:** 2 of 4 planned judges. Gemini Flash and DeepSeek V3 not run (missing API keys). Results should be interpreted as preliminary — 2 judges underpower the inter-judge agreement metric.

---

## Executive Summary

**The hypothesis was partially falsified.** With 2 frontier judges (GPT-4o and Claude Sonnet 4.6), semantic inter-judge agreement reached 88-94% — above the 90% falsification threshold in some conditions. However, three critical findings emerged:

1. **Numeric criteria show the most variance (70%)**, not semantic criteria as hypothesized
2. **Chain-of-thought prompting breaks structured output extraction** — GPT-4o extracted only 5 of 25 verdicts per response in Condition B
3. **Both judges are highly self-consistent (>95%)** — the variance is inter-judge, not intra-judge

The "structural variance" story is more nuanced than expected. The problem isn't that judges are random — it's that they're **systematically biased in different directions**, especially on quantitative judgment calls.

---

## 1. Inter-Judge Agreement by Criterion Type and Condition

| Criterion Type | A (Baseline) | C (Structured) | D (Few-Shot) | E (Specific Rubric) |
|:--------------|:---:|:---:|:---:|:---:|
| **Syntactic** | 88.3% | 87.2% | 99.1% | 91.7% |
| **Numeric** | **70.0%** | 80.0% | 90.0% | 90.0% |
| **Semantic** | 88.0% | 90.0% | — | 94.0% |

**Key finding:** Numeric criteria (margin plausibility, headcount math) show the LOWEST agreement at baseline (70%), not semantic criteria (88%). This contradicts the hypothesis that semantic = hardest to agree on.

**Condition B (Chain-of-Thought) excluded:** GPT-4o produced reasoning-heavy responses where JSON extraction failed, yielding only ~5 of 25 verdicts per call. This is itself a finding — CoT prompting is incompatible with reliable structured output extraction.

**Condition D (Few-Shot) had NaN for semantic** due to parsing inconsistencies (different criterion names in extracted JSON).

---

## 2. Intra-Judge Self-Consistency (Same Judge, Same Input, 3 Runs)

| Model | Syntactic | Numeric | Semantic |
|:------|:---:|:---:|:---:|
| Claude Sonnet | 98.1% | 96.7% | 99.3% |
| GPT-4o | 98.0% | 95.0% | 96.0% |

**Key finding:** Both judges are remarkably self-consistent (>95% across all types). The variance is NOT stochastic noise — it's systematic disagreement between judges. At temperature 0.3, each judge has a stable opinion. The problem is that the two judges' opinions diverge.

---

## 3. Accuracy vs Human Ground Truth (Averaged Across Judges)

| Criterion Type | A | C | D | E |
|:--------------|:---:|:---:|:---:|:---:|
| **Syntactic** | 91.6% | 91.5% | 97.1% | 91.7% |
| **Numeric** | 86.7% | 85.8% | 92.6% | 95.0% |
| **Semantic** | 94.0% | 95.0% | — | 95.7% |

**Key finding:** Accuracy is highest for semantic criteria (94-96%), meaning both judges tend to agree with the human expert on judgment calls. Numeric accuracy is lower (86-95%), suggesting the judges struggle more with quantitative verification than qualitative judgment.

---

## 4. Pairwise Judge Agreement

**Condition A (Baseline):** Claude Sonnet vs GPT-4o agree **90.4%** of the time.

This is above the 90% threshold, which means with only 2 frontier judges, agreement is high. Adding Gemini Flash and DeepSeek V3 would likely lower this — they're weaker models with different biases.

---

## 5. Statistical Test: Variance by Criterion Type

**Kruskal-Wallis H = 5.54, p = 0.0186**

- Mean variance score — Syntactic: 0.436, Semantic: 0.854
- Significant at p < 0.05 but **not at p < 0.01** (the pre-registered threshold)

The direction is right (semantic variance > syntactic), but the effect doesn't clear the bar with only 2 judges and 25 criteria. More judges would increase power.

---

## 6. Hypothesis Status (Pre-Registered Checks)

- [ ] **Semantic variance > 30pp higher than syntactic:** Gap = 0.3pp ❌ (effectively equal at 88% baseline)
- [x] **Prompting improvement A→E < 20pp on semantic:** Improvement = 6.0pp ✅
- [ ] **ANOVA p < 0.01:** p = 0.0186 ❌ (close but doesn't clear bar)
- [ ] **Intra-judge self-consistency < 85% for semantic:** 97.7% ❌ (judges are very self-consistent)

**Score: 1 of 4 criteria met.** Claim 1 is NOT supported as stated.

---

## 7. Falsification Check

- [x] Semantic agreement exceeded 90% in Condition E (specific rubric): **94.0%**

**⚠️ The hypothesis as stated is falsified** for 2 frontier judges. Semantic inter-judge agreement exceeds 90% with sufficiently specific rubrics.

---

## 8. What Actually Happened (Revised Interpretation)

The original hypothesis assumed semantic criteria would be the variance hotspot. The data tells a different story:

### The real variance story is about **numeric judgment**, not semantic judgment

Numeric criteria ("are margins within plausible range?", "does headcount math work?") require quantitative verification that frontier LLMs handle inconsistently:
- 70% baseline agreement vs 88% for semantic and syntactic
- This makes sense: "is 90% gross margin plausible?" requires domain knowledge about industry norms, while "does the balance sheet balance?" is pure arithmetic and "are assumptions well-documented?" is pattern matching

### CoT prompting is **anti-helpful** for structured evaluation

Condition B (chain-of-thought) was supposed to improve verdicts by forcing reasoning. Instead:
- GPT-4o produced verbose reasoning that buried the JSON, making extraction unreliable
- The model "thought itself out of" clear verdicts — reasoning introduced doubt and hedging
- This is a Tier 2 finding: prompting conditions that improve reasoning can degrade structured output

### Two frontier judges agree more than expected

90.4% pairwise agreement at baseline is high. Possible explanations:
1. GPT-4o and Claude Sonnet share training data patterns (RLHF convergence)
2. The rubric is well-specified enough that judgment space is narrow
3. Two judges is insufficient — need 4+ to surface real disagreement

### What this means for compiled verification

The argument shifts from "judges can't agree on semantic criteria" to:
1. **Numeric verification needs compilation** — the 70% baseline for numeric criteria is the real gap
2. **Extraction reliability matters more than verdict quality** — CoT breaking JSON extraction is a systems failure, not a judgment failure
3. **The variance surfaces with more judges** — 2 frontier judges is a weak test; DeepSeek and Gemini Flash would likely lower agreement significantly
4. **Self-consistency is a red herring** — each judge is consistent with itself, which means the biases are systematic and repeatable, but still divergent across judges

---

## 9. Recommended Next Steps

1. **Add 2 more judges** (Gemini Flash, DeepSeek V3) — the current N=2 is underpowered for inter-judge agreement claims
2. **Run E-C2 (tool calling)** — numeric criteria specifically to see if calculator tools close the 70% gap
3. **Pivot the article framing** — from "semantic variance is structural" to "numeric judgment and extraction reliability are the real institutional AI problems"
4. **Investigate the numeric criteria** — which specific checks caused the 70% disagreement? Margins? Headcount math? This tells us what to compile.

---

## 10. Raw Numbers for Reference

| Metric | Value |
|--------|-------|
| Total API calls | 300 (60 per condition) |
| Total evaluation rows | 6,462 |
| Judges | 2 (GPT-4o, Claude Sonnet 4.6) |
| Conditions | 5 (A through E; B partially failed) |
| Outputs evaluated | 10 (2 clear pass, 2 clear fail, 6 borderline) |
| Runs per combination | 3 |
| Crashes (rate limits) | 14 (all re-run successfully) |
| Zero-verdict responses | 0 for conditions A, C, E; significant data loss in B |

---

## 11. Appendix: Key Numbers for Article

The Substack article framing needs revision. Instead of the original:

> ~~"4 LLM judges agreed on semantic criteria only 47% of the time"~~

The actual finding:

> "Two frontier LLM judges agreed on numeric criteria — is this margin plausible? does this headcount math work? — only 70% of the time. On semantic criteria, they agreed 88%. The problem isn't that AI can't judge quality. It's that AI can't verify quantities. And chain-of-thought prompting, the standard fix, made things worse by breaking structured output extraction entirely."

This is a more interesting — and more honest — article.
