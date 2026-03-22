# E-C1: LLM Judge Variance Is Structural, Not Incidental

**Status:** Not Started
**Risk Level:** HIGH — This is the empirical foundation of the entire thesis
**Estimated Duration:** 3-5 days
**Dependencies:** None (start here)

---

## 1. Objective

Establish empirically that LLM-as-judge variance is a structural property of
inference-based evaluation — not a prompt engineering problem that can be
solved with better rubrics.

**Primary Questions:**
1. How much do different LLM judges disagree on the same output against the same rubric?
2. Does variance decrease substantially with better prompting (chain-of-thought, structured output)?
3. Is variance systematic (higher for semantic criteria, lower for syntactic)?
4. Does the same judge disagree with itself across runs (stochastic self-disagreement)?

**Null Hypothesis to Falsify:**
"LLM judge variance is primarily a prompting problem. With sufficiently structured rubrics and chain-of-thought prompting, inter-judge agreement exceeds 90%."

If the null hypothesis holds, compiled verification is solving the wrong problem.

---

## 2. Background

### 2.1 The LLM-as-Judge Paradigm

LLM-as-judge has become standard practice for evaluating agent outputs at scale.
The appeal: flexible, fast, no hand-coded rules, handles semantic criteria.

The concern: asking a stochastic model to evaluate another stochastic model.
There is no audit trail. Different judges produce different verdicts. The same
judge produces different verdicts on repeated runs. There is no ground truth
for the evaluation itself.

Prior work has shown inter-judge disagreement in academic settings (Zheng et al.,
"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena," 2023), but hasn't
specifically examined variance as a *structural* property vs a prompting artifact.

### 2.2 Why This Matters for Institutional AI

Sivulka (a16z, 2024) argues that institutional AI — AI operating inside companies
on high-stakes decisions — requires deterministic, auditable behavior. A validator
that sometimes passes and sometimes fails the same output is not a validator; it's
a coin flip with extra steps.

The question isn't whether LLM judges are *usually* right. It's whether they are
*reliably* right in the sense required for institutional trust.

### 2.3 The Intervention: Better Prompting

The standard response to judge variance is better prompting:
- Chain-of-thought: force the judge to reason step by step before deciding
- Structured output: require JSON with per-criterion verdicts
- Few-shot examples: anchor the judge's calibration
- Rubric specificity: add detail to reduce ambiguity

We test whether these interventions bring variance below an institutional threshold.

---

## 3. Experimental Design

### 3.1 The Rubric

Use the financial-model rubric from the validation-rubrics repo
(`https://github.com/a1j9o94/validation-rubrics`).

Financial model evaluation is the ideal test case:
- Mix of syntactic criteria (does the model balance? are formulas correct?)
- Mix of semantic criteria (is the growth assumption defensible? is sensitivity analysis thorough?)
- Real-world institutional stakes (wrong verdict = wrong investment decision)
- Existing ground truth available (the rubric itself is the spec)

**Rubric criteria taxonomy for this experiment:**

| Category | Description | Example Criteria |
|----------|-------------|-----------------|
| **Syntactic** | Objectively verifiable, no judgment required | Balance sheet balances, revenue = units × price, formulas reference correct cells |
| **Numeric** | Quantitative but require judgment about reasonableness | CAGR in defensible range (5-20% for SaaS), margins consistent with industry |
| **Semantic** | Require interpretation and judgment | Assumptions are well-documented, sensitivity analysis is thorough, model tells a coherent story |

### 3.2 The Test Outputs

Generate 10 financial model outputs with varying quality levels:
- 2 clearly correct (all criteria met)
- 2 clearly incorrect (major errors, clear failures)
- 6 borderline (some criteria met, some not, deliberate ambiguity)

The borderline cases are the test. Clear cases are calibration checks.

**Output generation method:**
1. Start from a real financial model template (3-statement model, SaaS)
2. Deliberately introduce specific errors (imbalanced balance sheet, unsupported growth rate, missing sensitivity analysis)
3. Generate borderline versions with partial compliance
4. Document ground truth for each criterion on each output (human expert)

### 3.3 The Judges

| Judge | Model | Provider | Notes |
|-------|-------|----------|-------|
| GPT-4o | gpt-4o-2024-11-20 | OpenAI | Standard frontier |
| Claude Sonnet 4.6 | claude-sonnet-4.6 | Anthropic/OpenRouter | Our default |
| Gemini 2.0 Flash | gemini-2.0-flash | Google/OpenRouter | Fast, cheap baseline |
| DeepSeek V3.2 | deepseek-v3.2 | DeepSeek/OpenRouter | Open-source frontier |

Each judge runs each output × each prompting condition × 3 repetitions.

### 3.4 Prompting Conditions

**Condition A: Baseline**
```
Evaluate this financial model against the following rubric.
For each criterion, output PASS or FAIL.

[Rubric]
[Model output]
```

**Condition B: Chain-of-Thought**
```
Evaluate this financial model against the following rubric.
For each criterion:
1. Quote the relevant section of the model
2. Explain your reasoning
3. Output PASS or FAIL

[Rubric]
[Model output]
```

**Condition C: Structured Output**
```json
{
  "rubric_evaluation": {
    "balance_sheet_balances": {"verdict": "PASS|FAIL", "evidence": "..."},
    "revenue_formula_correct": {"verdict": "PASS|FAIL", "evidence": "..."},
    ...
  }
}
```
Force JSON output format.

**Condition D: Few-Shot**
Provide 2 worked examples (one clear pass, one clear fail) before the test output.

**Condition E: Rubric Specificity**
Add explicit thresholds and definitions to every criterion:
- "Growth rate is defensible" → "Revenue CAGR between 5% and 25% for SaaS companies at Series B stage, with documented justification referencing comparable companies or market data"

### 3.5 Measurement

**Primary metrics:**

| Metric | Description | Formula |
|--------|-------------|---------|
| **Inter-judge agreement** | Do different judges agree on the same output? | % criteria where all 4 judges agree |
| **Intra-judge consistency** | Does the same judge agree with itself? | % criteria where same judge agrees across 3 runs |
| **Accuracy** | Does verdict match human ground truth? | % criteria matching human expert |
| **Variance by criterion type** | Does variance differ for syntactic vs semantic? | Separate agreement scores by category |

**Secondary metrics:**

| Metric | Description |
|--------|-------------|
| **False positive rate** | Judge says PASS when human says FAIL |
| **False negative rate** | Judge says FAIL when human says PASS |
| **Confidence calibration** | Do judge confidence scores predict accuracy? |
| **Prompting effect size** | How much does each condition reduce variance? |

**Data collection structure:**

```python
{
  "output_id": "fm-001",
  "output_quality": "borderline",
  "criterion": "balance_sheet_balances",
  "criterion_type": "syntactic",
  "human_ground_truth": "PASS",
  "judgments": {
    "gpt4o": {
      "condition_a": ["PASS", "PASS", "FAIL"],   # 3 runs
      "condition_b": ["PASS", "PASS", "PASS"],
      "condition_c": ["PASS", "PASS", "PASS"],
      "condition_d": ["PASS", "PASS", "PASS"],
      "condition_e": ["PASS", "PASS", "PASS"],
    },
    "claude_sonnet": { ... },
    "gemini_flash": { ... },
    "deepseek_v3": { ... },
  }
}
```

---

## 4. Hypothesized Results

### What We Expect (If Hypothesis Is Correct)

```
Inter-judge agreement by criterion type and prompting condition:

                    Condition A   Condition B   Condition C   Condition E
                    (Baseline)    (CoT)         (Structured)  (Specific rubric)

Syntactic criteria     85%           88%            91%           95%
Numeric criteria       65%           70%            72%           78%
Semantic criteria      45%           50%            52%           58%

Human agreement (acc): 
Syntactic              88%           90%            92%           93%
Numeric                70%           73%            74%           76%
Semantic               52%           55%            55%           57%
```

**Key pattern to look for:**
- Syntactic: high agreement, converges toward 95%+ with better prompting. Near-solved by Tier 2.
- Semantic: persistent variance around 50-60% regardless of prompting. Not a prompting problem.

### Intra-Judge Self-Consistency

```
Same judge, same input, 3 runs:

           Syntactic   Numeric    Semantic
GPT-4o     97%         88%        72%
Sonnet      98%         90%        74%
Gemini      95%         83%        65%
DeepSeek    94%         85%        68%
```

Even the same model disagrees with itself on semantic criteria ~25-35% of the time.

### What Would Falsify the Hypothesis

```
Inter-judge agreement with specific rubrics (Condition E):

Syntactic    >95%   → expected, doesn't falsify
Numeric      >90%   → better than expected, but tolerable
Semantic     >90%   → FALSIFIES HYPOTHESIS

If semantic agreement > 90% with good prompting, the problem is solvable
at Tier 1. No need for compiled verification.
```

---

## 5. Analysis Plan

### 5.1 Primary Analysis: Agreement Heatmap

Produce an inter-judge agreement matrix for each prompting condition:

```
           GPT-4o   Sonnet   Gemini   DeepSeek
GPT-4o      —        82%      74%      79%
Sonnet      82%      —        71%      77%
Gemini      74%      71%      —        73%
DeepSeek    79%      77%      73%      —

Average pair agreement: 76% (baseline)
```

### 5.2 Criterion-Level Analysis

For each criterion, compute:
- Variance score (0-1): how much do judges disagree?
- Type label: syntactic / numeric / semantic
- Prompting sensitivity: does it improve with better conditions?

Plot: variance score vs criterion type, colored by prompting sensitivity.

### 5.3 The "Residual Variance" Test

After applying the best prompting condition (Condition E), compute residual variance.

**If residual variance on semantic criteria > 15% across judges:**
→ Structural, not prompting-solvable.

**If residual variance on semantic criteria < 5% with Condition E:**
→ Prompting is sufficient. Hypothesis falsified.

### 5.4 Correlation with Criterion Type

Run ANOVA or Kruskal-Wallis:
- Null: variance is uniform across criterion types
- Alternative: semantic criteria show significantly higher variance than syntactic

We expect p < 0.01 for the difference between syntactic and semantic variance.

---

## 6. Success Metrics

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Syntactic inter-judge agreement (Condition A) | > 85% | Expected — calibration check |
| Semantic inter-judge agreement (Condition A) | < 70% | Structural variance exists |
| Semantic improvement from A → E | < 20pp | Prompting alone can't fix it |
| Intra-judge self-consistency, semantic | < 85% | Even one model is unreliable |
| ANOVA p-value (syntactic vs semantic variance) | < 0.01 | Variance is type-dependent |

If all five thresholds are met: **Claim 1 is supported.** Proceed to E-C2.

---

## 7. Failure Criteria

Claim 1 is **not supported** if:

1. Semantic inter-judge agreement > 85% in Condition A — judges agree by default
2. Semantic agreement improves to > 90% in Condition E — prompting solves it
3. ANOVA finds no significant difference between syntactic and semantic variance
4. All judges agree with human ground truth > 90% across all criterion types

In any of these cases, the problem is prompting quality, not structural limitation.
Write this up as a finding (LLM judges are more reliable than assumed) and pivot
the article away from compiled verification as a necessity.

---

## 8. Implementation Plan

### 8.1 Setup (Day 1)

```bash
# Repository structure
compiled-verification/
  research/
    experiments/
      e-c1-judge-variance/
        data/
          outputs/        # 10 financial model outputs (text)
          ground-truth/   # Human expert verdicts, per criterion
          results/        # Raw judge responses
        scripts/
          generate_outputs.py
          run_judges.py
          analyze_results.py
        notebooks/
          analysis.ipynb
        FINDINGS.md
```

**Dependencies:**
```bash
pip install openai anthropic google-generativeai
pip install pandas numpy scipy matplotlib seaborn
pip install python-dotenv  # for API keys
```

### 8.2 Generate Test Outputs (Day 1-2)

Start from a 3-statement SaaS financial model template. Generate 10 variants:

| ID | Quality | Deliberate Issues |
|----|---------|-------------------|
| fm-001 | Clear pass | None |
| fm-002 | Clear pass | None |
| fm-003 | Clear fail | Balance sheet doesn't balance, growth rate 200% |
| fm-004 | Clear fail | No sensitivity analysis, circular references |
| fm-005 | Borderline | Balance sheet balances, growth undocumented |
| fm-006 | Borderline | Good structure, aggressive assumptions |
| fm-007 | Borderline | Missing one statement, good narrative |
| fm-008 | Borderline | Numbers correct, no cash flow statement |
| fm-009 | Borderline | Good model, weak sensitivity analysis |
| fm-010 | Borderline | Complete model, internally inconsistent story |

Human expert reviews each output and documents ground truth per criterion.

### 8.3 Run Judges (Day 2-3)

```python
import openai
import anthropic
from itertools import product

models = ["gpt-4o", "claude-sonnet-4-6", "gemini-2.0-flash", "deepseek-v3.2"]
conditions = ["A", "B", "C", "D", "E"]
outputs = load_outputs()  # 10 financial models
rubric = load_rubric()    # from validation-rubrics repo

results = []
for output, model, condition in product(outputs, models, conditions):
    for run in range(3):  # 3 repetitions
        prompt = build_prompt(output, rubric, condition)
        verdict = call_model(model, prompt)
        results.append({
            "output_id": output.id,
            "model": model,
            "condition": condition,
            "run": run,
            "verdicts": parse_verdicts(verdict)
        })

save_results(results)
```

Total API calls: 10 outputs × 4 models × 5 conditions × 3 runs = 600 calls
Estimated cost: ~$30-50 total (mostly GPT-4o)

### 8.4 Analysis (Day 3-4)

```python
import pandas as pd
from scipy.stats import kruskal

df = load_results()

# Inter-judge agreement per condition
for condition in conditions:
    cond_df = df[df.condition == condition]
    agreement = compute_inter_judge_agreement(cond_df)
    print(f"Condition {condition}: {agreement:.1%}")

# Variance by criterion type
for ctype in ["syntactic", "numeric", "semantic"]:
    type_df = df[df.criterion_type == ctype]
    variance = compute_variance(type_df)
    print(f"{ctype}: variance = {variance:.2f}")

# ANOVA: is variance type-dependent?
syntactic_vars = df[df.criterion_type == "syntactic"].groupby("criterion").apply(variance_score)
semantic_vars = df[df.criterion_type == "semantic"].groupby("criterion").apply(variance_score)
stat, p = kruskal(syntactic_vars, semantic_vars)
print(f"Kruskal-Wallis: H={stat:.2f}, p={p:.4f}")
```

### 8.5 Write FINDINGS.md (Day 5)

Document:
1. Primary result: inter-judge agreement by type and condition (tables + heatmaps)
2. Falsification check: did variance converge with better prompting?
3. Residual variance analysis: what's left after best prompting?
4. Implications for the article's four-tier framework

---

## 9. Timeline

| Day | Activity | Deliverable |
|-----|----------|-------------|
| 1 | Setup repo structure, dependencies, rubric extraction | Working script scaffold |
| 2 | Generate 10 financial model outputs, human ground truth | `data/outputs/`, `data/ground-truth/` |
| 3 | Run all judges across all conditions | `data/results/` (600 API calls) |
| 4 | Analysis: agreement matrices, ANOVA, residual variance | Figures + tables |
| 5 | Write FINDINGS.md, update core hypothesis, note implications | FINDINGS.md |

---

## 10. Deliverables

### D1: Raw Data
- 10 financial model outputs (text files)
- Human expert verdicts (per criterion, per output)
- Raw judge responses (600 calls, JSON)

### D2: Analysis Notebook
- `notebooks/analysis.ipynb`
- All figures, tables, statistical tests
- Reproducible from raw data

### D3: FINDINGS.md
Format: matches foresight experiment findings (see `foresight/research/experiments/c1-vlm-latent-sufficiency/FINDINGS.md`)

### D4: Article-Ready Data Points
- 2-3 specific numbers ready for the Substack piece
- Example: "Across 10 financial model evaluations, 4 LLM judges agreed on all semantic criteria only 47% of the time. Chain-of-thought prompting raised this to 53%. The ceiling is structural, not prompting."

---

## 11. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Judges agree too well (hypothesis falsified) | Low | High | Write as positive finding; pivot article framing |
| Ground truth ambiguity (human expert disagrees with self) | Medium | Medium | Two human raters, compute inter-human agreement as baseline |
| API costs exceed estimate | Low | Low | Budget $100; kill after $75 |
| Rubric criteria too syntactic (all criteria compile) | Medium | Medium | Ensure semantic criteria included; verify with human review |

---

## 12. Connection to Article

This experiment produces the **empirical stake in the ground** for the Substack piece.

The article's opening argument — "LLM-as-judge is probabilistic and structurally insufficient" — needs data, not just assertion. E-C1 produces specific numbers:

> "I tested 4 LLM judges against the same financial model rubric. On syntactic criteria — does the balance sheet balance, do the formulas reference the right cells — they agreed 91% of the time. On semantic criteria — are the growth assumptions defensible, does the model tell a coherent story — they agreed 47% of the time. Chain-of-thought prompting moved this to 53%. Better rubric specificity: 58%. The ceiling is not a prompting problem. It's structural."

That paragraph becomes the empirical foundation for everything that follows.

---

## See Also

- [Core Hypothesis](core-hypothesis.md)
- [E-C2: Tool Calling Limits](e-c2-tool-calling-limits.md)
- [E-C3: TRACR Prototype](e-c3-tracr-prototype.md)
- [validation-rubrics repo](https://github.com/a1j9o94/validation-rubrics)
- [Synthesis: Hypernetworks and Percepta](../papers/hypernetworks-percepta-synthesis.md)

---

**Document Version:** 1.0
**Created:** 2026-03-22
**Author:** Collie (compiled-verification research)
