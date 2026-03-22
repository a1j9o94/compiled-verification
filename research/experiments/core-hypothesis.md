# Core Hypothesis: Compiled Verification

## Primary Hypothesis

> LLM-as-judge validation is not just imperfect — it is structurally insufficient for institutional AI. Validation rubrics can and should be compiled into deterministic artifacts rather than interpreted by probabilistic models.

## Why This Might Be True

The institutional AI thesis (Sivulka/Hebbia via a16z) argues that high-stakes AI deployment requires deterministic, auditable agents — not just "probably correct" outputs. Current eval frameworks (LLM-as-judge, rubric prompts) are flexible but unverifiable: one stochastic model evaluating another, with no audit trail.

TRACR (Lindner et al., 2023) proves that algorithms can be compiled into exact transformer weights. Percepta (Tzamos, 2026) proves that transformer forward passes can execute programs efficiently. Together they point toward a new paradigm: validation rubrics compiled to deterministic checkers rather than interpreted by probabilistic judges.

Our hypothesis: **the variance in LLM-as-judge verdicts is not random noise — it is a structural property of inference-based validation that cannot be engineered away. Compiled validation is the correct fix, not better prompting.**

---

## Four-Tier Framework

```
Tier 1: LLM-as-Judge           — probabilistic, unverifiable
         ↓ what's wrong with it?
Tier 2: Tool Calling            — deterministic ops, stochastic orchestration
         ↓ what's the limit?
Tier 3: In-Model Computation    — forward pass IS computation (Percepta)
         ↓ what does this enable?
Tier 4: Compiled Verification   — rubric → deterministic validator artifact
```

Each tier is testable. We test Tier 1's failure mode empirically. Tiers 2-4 are
analyzed theoretically and demonstrated with prototypes.

---

## Testable Claims

We break the primary hypothesis into **four independent claims**, each testable
in isolation.

### Claim 1: LLM-Judge Variance Is Structural, Not Incidental
📋 **[Detailed Experiment Plan](e-c1-judge-variance.md)**

**Statement:** When multiple LLM judges evaluate the same output against the same rubric, their verdicts vary in ways that cannot be reduced by better prompting alone. The variance is a property of inference-based evaluation, not prompt quality.

**Why this matters:** If variance is just a prompting problem, better rubric engineering solves it. If it's structural, compiled verification is the correct fix.

**Independent Test:**
```
Input:  Same agent output (financial model) + same rubric
Models: GPT-4o, Claude Sonnet 4.6, Gemini 2.0 Flash, DeepSeek V3
Output: Pass/fail verdicts + confidence scores
Compare: Inter-judge agreement, variance analysis
```

**Success criterion:** Statistically significant variance across judges on the same input, AND variance does not decrease substantially with better prompting (chain-of-thought, structured output, etc.).

**Failure mode:** All judges agree consistently → prompting alone is sufficient → compiled verification not necessary.

---

### Claim 2: Tool Calling Reduces But Does Not Eliminate Stochasticity
📋 **[Detailed Experiment Plan](e-c2-tool-calling-limits.md)**

**Statement:** When judges are given tool-calling capabilities (code execution, calculators), their verdicts on syntactic/numeric criteria converge — but their verdicts on semantic criteria remain variable. The deterministic boundary is narrow.

**Why this matters:** Establishes where tool calling helps and where it doesn't. Defines the ceiling of Tier 2.

**Independent Test:**
```
Condition A: Judge evaluates numeric rubric criteria (word count, citation count)
             with and without code execution tools
Condition B: Judge evaluates semantic rubric criteria (tone, relevance, quality)
             with and without code execution tools
Compare: Variance reduction in Condition A vs B
```

**Success criterion:** Variance near-zero for syntactic criteria with tools. Variance persists for semantic criteria.

**Failure mode:** Tools solve both syntactic AND semantic variance → Tier 2 is sufficient.

---

### Claim 3: TRACR-Style Compilation Produces Exact Validators for Syntactic Criteria
📋 **[Detailed Experiment Plan](e-c3-tracr-prototype.md)**

**Statement:** A TRACR-compiled transformer can check structural rubric criteria (citation count ≥ 3, word count ≤ 500, formatting compliance) exactly, with 100% agreement across runs and zero variance.

**Why this matters:** Establishes that compiled verification is feasible in practice, not just theoretically. Demonstrates the determinism that LLM judges lack.

**Independent Test:**
```
Input:  Same agent outputs as Claim 1
Process: Compile rubric criteria → TRACR weights → run validator
Output: Pass/fail verdicts
Compare: 100% consistency across multiple runs? Matches ground truth?
```

**Success criterion:** Zero variance across runs. 100% accuracy on syntactic criteria verifiable by human inspection.

**Failure mode:** TRACR compilation too brittle / limited for real rubric criteria.

---

### Claim 4: Hybrid Architecture Outperforms Pure LLM-Judge
📋 **[Detailed Experiment Plan](e-c4-hybrid-architecture.md)**

**Statement:** A hybrid validator (compiled checker for syntactic criteria + LLM judge for semantic criteria) produces more consistent verdicts than a pure LLM judge, with a smaller, auditable stochastic surface.

**Why this matters:** Demonstrates that partial compiled verification is practically useful even before full semantic compilation is possible.

**Independent Test:**
```
Condition A: Pure LLM-judge (4 models × N outputs)
Condition B: Hybrid (compiled syntactic + LLM semantic)
Condition C: Ground truth (human expert verdicts)
Compare: Agreement with ground truth, inter-rater consistency, error analysis
```

**Success criterion:** Hybrid agrees with human ground truth more consistently than pure LLM judge. The LLM surface in the hybrid is smaller and more targeted.

**Failure mode:** LLM semantic variance dominates — hybrid not meaningfully better than pure judge.

---

## Open Research Questions

### Q1: What Is the Computational Class of Practically Compilable Validators?
📋 **[Detailed Experiment Plan](e-q1-computational-class.md)**

**Question:** TRACR can compile finite-depth RASP programs. Giannou et al. prove universal computation with looped transformers. Where do real rubric criteria fall? What fraction of practical rubric checks are compilable today?

**Experiments:**
1. Categorize 50 real rubric criteria from validation-rubrics repo by type (syntactic/semantic/hybrid)
2. Attempt to express each syntactic criterion in RASP
3. Measure: what % can be fully formalized? What's the failure mode for the rest?

**Why it matters:** Defines the scope of compiled verification today and what would expand it.

---

### Q2: Can a Hypernetwork Learn to Compile?
📋 **[Detailed Experiment Plan](e-q2-hypernetwork-compiler.md)**

**Question:** Rather than hand-writing a compiler (TRACR), can we train a hypernetwork that takes a rubric embedding and generates the weights of a small validator network? This is the path from Tier 3 to Tier 4.

**Why it matters:** TRACR requires manual formalization of each criterion. A learned hypernetwork compiler would generalize across rubrics from natural language.

**Feasibility signals from literature:**
- Ha et al. (2016): hypernetworks generate weights from conditioning vectors ✓
- Liao et al. (2023): hypernetworks discover novel algorithms for L1 norm ✓
- Von Oswald et al. (2020): task-conditioned weight generation ✓
- TRACR: exact compilation from formal spec (but not NL) ✓

**The gap:** NL rubric → formal spec → weights. Step 1 is unsolved.

---

### Q3: Does Inter-Judge Variance Correlate with Rubric Criterion Type?
📋 **[Linked to e-c1-judge-variance.md]**

**Question:** Is LLM-judge variance systematic — higher for semantic criteria, lower for syntactic? Or is it random noise across all criteria types?

**Why it matters:** If variance is systematic, compiled verification targets the right surface. If it's random, the problem is different.

---

## End-to-End Evaluation

Once components are validated, test the full compiled-verification pipeline:

**Task:** Agent produces financial model analysis. Validate against the financial-model rubric from the validation-rubrics repo.

**Conditions:**

| Condition | Description |
|-----------|-------------|
| Pure LLM Judge (4 models) | Baseline — measures variance |
| LLM Judge + CoT | Tests if better prompting reduces variance |
| LLM Judge + Tools | Tests Tier 2 ceiling |
| TRACR compiled (syntactic only) | Tests Claim 3 |
| Hybrid (compiled + LLM semantic) | Tests Claim 4 |
| Human expert | Ground truth |

**Primary metric:** Agreement with human expert ground truth.
**Secondary metric:** Inter-run consistency (same input, run 5 times, how often does verdict change?).

---

## Falsification Criteria

The primary hypothesis is **falsified** if ANY of:

1. **LLM judges agree consistently:** Inter-judge agreement > 90% on the same inputs with simple prompting → variance is a prompting problem, not structural.

2. **Tool calling eliminates variance for semantic criteria:** If judges with code execution agree on semantic checks → Tier 2 is sufficient.

3. **TRACR compilation fails for all practical rubric criteria:** If no real rubric criteria can be expressed in RASP → compiled verification is not feasible.

4. **Hybrid is not better than pure LLM judge:** If the hybrid doesn't improve agreement with human ground truth → the architecture doesn't help.

---

## Experiment Sequence

Ordered to fail fast:

### Phase 1: Establish the Problem (Week 1)
| Experiment | Go/No-Go |
|------------|----------|
| E-C1: LLM judge variance | Does variance exist and is it substantial? |

*If judges agree consistently → hypothesis is wrong. Stop.*

### Phase 2: Map the Ceiling of Current Approaches (Week 2)
| Experiment | Go/No-Go |
|------------|----------|
| E-C2: Tool calling limits | Does Tier 2 solve semantic variance? |
| E-Q3: Variance by criterion type | Is variance systematic? |

*If tool calling solves all variance → published finding, write it up.*

### Phase 3: Demonstrate Compiled Verification (Week 3-4)
| Experiment | Go/No-Go |
|------------|----------|
| E-Q1: Computational class survey | How many real criteria are compilable? |
| E-C3: TRACR prototype | Can we build a compiled checker that works? |

### Phase 4: Hybrid Architecture (Week 4-5)
| Experiment | Measures |
|------------|----------|
| E-C4: Hybrid vs pure judge | Does the hybrid win? By how much? |

---

## Evolution Log

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-03-22 | Initial hypothesis from Substack article planning. Four-tier framework. |

## Related Documents

- [Literature Review](../papers/hypernetworks-percepta-synthesis.md)
- [E-C1: LLM Judge Variance](e-c1-judge-variance.md)
- [validation-rubrics repo](https://github.com/a1j9o94/validation-rubrics)
- Substack: "Compiled Verification: From Judgment to Proof" (in progress)
