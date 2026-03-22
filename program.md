# Compiled Verification — Experiment Program

This is the research org specification for the compiled-verification project.
Inspired by Karpathy's autoresearch pattern: the human writes instructions,
the agent runs science.

## What This Project Is

We are testing the hypothesis that LLM-as-judge validation is structurally
insufficient for institutional AI — and that compiled, deterministic validators
are the correct fix.

**The four-tier thesis:**
```
Tier 1: LLM-as-Judge        → probabilistic, unverifiable
Tier 2: Tool Calling        → deterministic ops, stochastic orchestration
Tier 3: In-Model Computation → forward pass IS computation (Percepta)
Tier 4: Compiled Validation  → rubric compiled to deterministic validator artifact
```

Our experiments test Tiers 1-2 empirically and prototype Tiers 3-4.

## The Invariants (Never Modify)

These are fixed ground truth. Do not touch:

- **`research/papers/`** — lit review files are read-only reference
- **`research/experiments/e-c1-judge-variance/data/ground-truth/`** — human expert verdicts. These are the frozen eval. An agent cannot modify its own eval.
- **The rubric source:** `https://github.com/a1j9o94/validation-rubrics` — used as-is

## The Experimental Surface

Everything else is fair game:
- Prompting conditions (conditions A-E in E-C1)
- Judge model selection
- Analysis methods
- Prototype architectures

## The Experiment Loop (for autonomous runs)

```
LOOP:
1. Read current experiment plan from research/experiments/e-c1-judge-variance.md
2. Run the next condition/judge combination not yet in results/
3. Save raw output to data/results/<model>-<condition>-run<n>.json
4. Update results/summary.tsv
5. If all conditions complete → run analysis, write FINDINGS.md
6. NEVER modify data/ground-truth/ — it is the frozen eval harness
7. NEVER ask if you should continue — run until manually stopped
```

## Logging Format

`research/experiments/e-c1-judge-variance/data/results/summary.tsv`

```
model	condition	run	output_id	criterion	criterion_type	verdict	ground_truth	match
gpt-4o	A	1	fm-001	balance_sheet	syntactic	PASS	PASS	1
```

Each experiment run is a git commit. The branch history is the experiment log.

## Crash Handling

- API timeout → retry once, then log as crash and skip
- JSON parse failure → log raw response and crash
- Model refuses to evaluate → try alternate phrasing, then skip
- Never ask the human for guidance during a run

## Output Quality Bar

A condition is "complete" when:
- All 10 outputs evaluated
- All criteria scored
- 3 runs completed per condition
- `summary.tsv` updated

Do not move to the next condition until current is complete.

## The Simplicity Criterion (from Karpathy)

When evaluating approaches: if a simpler method gets within 95% of quality,
prefer the simpler method. Applied here: if basic prompting (Condition A) gets
inter-judge agreement > 90% on semantic criteria, document it and stop —
compiled verification is solving the wrong problem.

## Reading List (before running experiments)

1. `research/experiments/core-hypothesis.md` — the full hypothesis
2. `research/experiments/e-c1-judge-variance.md` — E-C1 detailed plan
3. `research/papers/hypernetworks-percepta-synthesis.md` — theoretical foundation
