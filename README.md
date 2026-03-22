# Compiled Verification

Research into deterministic, auditable verification for AI agent output.

## The Thesis

Current AI validation is probabilistic all the way down. LLM-as-judge gives you one stochastic model evaluating another. Tool calling gets you one island of determinism inside stochastic orchestration. Neither is sufficient for institutional AI.

The question this repo explores: can validation rubrics be *compiled* into deterministic artifacts rather than *interpreted* by probabilistic models?

The four-tier progression:
1. **Inference validation** — LLM-as-judge. Flexible, unverifiable. Turtles all the way down.
2. **Tool calling** — deterministic operations, stochastic orchestration. A half-measure.
3. **In-model computation** — Percepta shows the forward pass can *be* computation, not just inference. Execution trace = audit log.
4. **Compiled validation** — if the forward pass is computation, can it produce a compiled validator artifact? Hypernetworks + TRACR point toward yes.

## Structure

```
research/
  papers/          # Deep literature reviews (foresight format)
  experiments/     # Empirical work (LLM-judge variance, etc.)
  hypotheses/      # Core hypotheses and open questions
writing/           # Substack drafts
  compiled-verification-draft.md
```

## Related

- [validation-rubrics](https://github.com/a1j9o94/validation-rubrics) — practical framework this builds on
- [Percepta blog post](https://www.percepta.ai/blog/can-llms-be-computers) — Tier 3 foundation
- Substack: "Your AI Agents Need an Audit Committee" (published) → "Compiled Verification: From Judgment to Proof" (in progress)
