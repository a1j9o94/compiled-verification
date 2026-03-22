# CLAUDE.md — Compiled Verification

You are a research agent working on the compiled-verification project.
Read this file fully before doing anything else.

## What This Project Is

We are testing whether LLM-as-judge validation is structurally insufficient
for institutional AI — and whether compiled, deterministic validators are the
correct fix.

**The four-tier thesis:**

```
Tier 1: LLM-as-Judge         → probabilistic, unverifiable (turtles all the way down)
Tier 2: Tool Calling         → deterministic ops, stochastic orchestration (half-measure)
Tier 3: In-Model Computation → forward pass IS computation (Percepta, 2026)
Tier 4: Compiled Validation  → rubric compiled into a deterministic validator artifact
```

Tiers 1-2 are tested empirically. Tiers 3-4 are analyzed theoretically and prototyped.

## Repo Structure

```
CLAUDE.md                          ← you are here
README.md                          ← project overview
program.md                         ← experiment loop protocol (read this too)

research/
  papers/                          ← 8 deep lit reviews + synthesis (READ-ONLY)
    hypernetworks-ha-2016.md
    fast-weight-programmers-schlag-2021.md
    hypernetworks-continual-learning-oswald-2020.md
    hypernetworks-interpretable-algorithms-liao-2023.md
    percepta-tzamos-2026.md
    looped-transformers-giannou-2023.md
    tracr-lindner-2023.md
    icl-as-gradient-descent-dai-2022.md
    hypernetworks-percepta-synthesis.md  ← START HERE for theory

  experiments/
    core-hypothesis.md             ← four testable claims, falsification criteria
    e-c1-judge-variance.md         ← NEXT EXPERIMENT (fully designed, ready to run)
    e-c1-judge-variance/
      FINDINGS.md                  ← populate after running
      data/
        outputs/                   ← 10 financial model outputs (generate these)
        ground-truth/              ← human expert verdicts (FROZEN — never modify)
        results/                   ← raw judge API responses

writing/                           ← Substack draft (in progress)
```

## What's Been Done

- [x] Literature review: 8 paper reviews covering hypernetworks, Percepta, TRACR, fast weight programmers, looped transformers, ICL-as-gradient-descent
- [x] Synthesis doc establishing four-tier argument is technically sound
- [x] Core hypothesis doc with 4 testable claims and falsification criteria
- [x] E-C1 fully designed (see `research/experiments/e-c1-judge-variance.md`)
- [x] program.md written (autoresearch-style experiment loop protocol)
- [ ] E-C1 data generation (10 financial model outputs + human ground truth)
- [ ] E-C1 experiment run (600 API calls across 4 judges × 5 conditions × 3 runs)
- [ ] E-C1 analysis and FINDINGS.md
- [ ] E-C2 through E-C4 experiment plans
- [ ] Substack draft

## What To Do Next

**If picking up fresh: run E-C1.**

1. Read `research/experiments/e-c1-judge-variance.md` for full design
2. Generate 10 financial model outputs in `data/outputs/` (SaaS 3-statement model, varying quality — 2 clear pass, 2 clear fail, 6 borderline)
3. Record human expert ground truth verdicts per criterion in `data/ground-truth/` — this is the FROZEN eval. Do not touch after this point.
4. Pull the financial-model rubric from https://github.com/a1j9o94/validation-rubrics
5. Run all 4 judges × 5 conditions × 3 runs, save JSON to `data/results/`
6. Analyze: inter-judge agreement by criterion type and prompting condition
7. Write FINDINGS.md — especially the "key numbers for article" section

## The Invariants — Never Touch

- `research/papers/` — read-only reference material
- `research/experiments/e-c1-judge-variance/data/ground-truth/` — frozen eval harness. Modifying this after judges have run invalidates the experiment.
- The rubric from validation-rubrics repo — used as-is, no modifications

## Key Design Principles (from Karpathy autoresearch)

1. **Frozen eval harness** — ground truth is set before any judge runs. The agent cannot modify its own eval. This is clinical trial blinding applied to our experiment.

2. **Single primary metric** — inter-judge agreement % is the number everything reduces to. Secondary metrics (accuracy vs human, false positive rate) are supporting.

3. **Git as experiment log** — each condition batch is a commit. Branch history = experiment history. `results/summary.tsv` is the human-readable parallel (untracked).

4. **Simplicity criterion** — if basic prompting (Condition A) yields semantic inter-judge agreement > 90%, the hypothesis is falsified. Document it and stop. Don't let the research agenda survive contrary evidence.

5. **Never stop, never ask** — run the experiment loop autonomously. If an API call fails, retry once then log as crash and skip. Don't ask for guidance mid-run.

## The Article This Feeds

Substack: **"Compiled Verification: From Judgment to Proof"**

Follow-up to "Your AI Agents Need an Audit Committee" (published).

The article's empirical spine is E-C1's key data point:
> "Across 10 financial model evaluations, 4 LLM judges agreed on semantic
> criteria only X% of the time. Chain-of-thought prompting raised this to Y%.
> The ceiling is structural."

The theoretical arc: inference → tool calling → Percepta → hypernetworks/TRACR.
The synthesis is in `research/papers/hypernetworks-percepta-synthesis.md`.

## Related Repos

- https://github.com/a1j9o94/validation-rubrics — rubric source (the practical framework)
- https://github.com/a1j9o94/foresight — separate project (world models / video reasoning, unrelated)
- https://github.com/karpathy/autoresearch — design pattern inspiration
