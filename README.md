# Compiled Verification

Research into deterministic, auditable verification for AI agent output.

## The Thesis

Current AI validation is probabilistic all the way down. LLM-as-judge gives you one stochastic model evaluating another. Tool calling gets you one island of determinism inside stochastic orchestration. Neither is sufficient for institutional AI.

The question this repo explores: can validation rubrics be *compiled* into deterministic artifacts rather than *interpreted* by probabilistic models?

**The four-tier argument:**

| Tier | Approach | Problem |
|------|----------|---------|
| 1 | LLM-as-Judge | Probabilistic, unverifiable. Turtles all the way down. |
| 2 | Tool Calling | Deterministic ops, stochastic orchestration. A half-measure. |
| 3 | In-Model Computation | Forward pass IS computation (Percepta, 2026). Execution trace = audit log. |
| 4 | Compiled Validation | Rubric → deterministic validator artifact. Hypernetworks + TRACR point here. |

## Status

| Work | Status |
|------|--------|
| Literature review (8 papers) | ✅ Complete |
| Theoretical synthesis | ✅ Complete |
| Core hypothesis + falsification criteria | ✅ Complete |
| E-C1 experiment design | ✅ Complete |
| E-C1 data generation | ⬜ Not started |
| E-C1 experiment run | ⬜ Not started |
| E-C2 through E-C4 designs | ⬜ Not started |
| Substack draft | ⬜ Not started |

## Quick Start

Read `CLAUDE.md` for the full research context and what to do next.

The first experiment to run is **E-C1** (`research/experiments/e-c1-judge-variance.md`):
- 10 financial model outputs × 4 LLM judges × 5 prompting conditions × 3 runs
- ~600 API calls, ~$30-50 total
- Produces the empirical foundation for the Substack article

## Structure

```
CLAUDE.md                    ← agent onboarding (start here)
program.md                   ← experiment loop protocol
research/
  papers/                    ← 8 deep lit reviews + synthesis
  experiments/               ← hypothesis doc + experiment plans + results
writing/                     ← Substack draft (in progress)
```

## Related

- [validation-rubrics](https://github.com/a1j9o94/validation-rubrics) — rubric source, the practical framework this builds on
- [Percepta: Can LLMs Be Computers?](https://www.percepta.ai/blog/can-llms-be-computers) — Tier 3 foundation
- [karpathy/autoresearch](https://github.com/karpathy/autoresearch) — experiment loop design inspiration
- Substack predecessor: ["Your AI Agents Need an Audit Committee"](https://a1j9o94.substack.com) (published)
