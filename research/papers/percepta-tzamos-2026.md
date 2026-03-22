# Can LLMs Be Computers?

**Authors:** Christos Tzamos and team at Percepta
**Year:** 2026 (March 11, 2026)
**Venue:** Percepta Field Notes (blog post / technical report)
**Links:** [Post](https://www.percepta.ai/blog/can-llms-be-computers)

## Summary

Percepta demonstrates that a **standard PyTorch transformer can execute arbitrary programs internally**, without external tool calls. They implement a WebAssembly interpreter inside transformer weights, enabling the model to execute compiled C code step by step within its own forward pass. The key technical innovation is **2D attention heads** that enable O(log t) decoding via convex hull queries, replacing the standard O(t) attention scan. This makes million-step execution traces practical.

The system achieves 34,000+ tokens/sec on CPU, solves the "hardest Sudoku in the world" (Arto Inkala's) in under 3 minutes, and computes min-cost perfect matching via the Hungarian algorithm — all without any external tool invocation.

## Key Technical Insights

### The Core Problem: LLMs Can't Compute

Despite solving IMO-level math problems, LLMs fail at basic computation:
- Can't reliably add large numbers
- Can't solve hard Sudoku puzzles
- Must delegate to external tools (code interpreters, calculators)

Current workarounds (tool use, agentic orchestration) keep computation **outside** the model. The model specifies computation but doesn't execute it.

### In-Model Execution vs Tool Use

```
TOOL USE (current paradigm):
  Model → writes code → [external interpreter] → result injected back
  The model never "sees" the computation happening.

IN-MODEL EXECUTION (Percepta):
  Model → emits WebAssembly program → executes it step-by-step
  → every intermediate step appears in the output token stream
  The model IS the computer.
```

### The Architecture: Vanilla Transformer with 2D Heads

```python
class VanillaTransformer(nn.Module):
    def __init__(self, vocab, d_model=36, n_heads=18, n_layers=7, d_ffn=36):
        # d_model=36, n_heads=18 → head_dim = 2
        # 7 layers, standard nn.MultiheadAttention
        # Gated FFN with ReLU
        # NO custom attention kernels, NO sparse masks
```

**The only special thing is the weights.** The architecture is completely standard PyTorch.

### 2D Attention Heads and HullKVCache

The critical innovation: restricting attention head dimension to 2 enables a geometric interpretation:

```
    2D ATTENTION AS CONVEX HULL QUERY
    ┌──────────────────────────────────────────┐
    │                                          │
    │   Each key k_j ∈ ℝ²  (a point in 2D)    │
    │   Query q ∈ ℝ²  (a direction in 2D)     │
    │                                          │
    │   Hard-max attention = find point on     │
    │   convex hull furthest in direction q    │
    │                                          │
    │        *  k₃                             │
    │       / \                                │
    │      /   \     ← convex hull             │
    │   k₁*     *k₅                            │
    │      \   /                               │
    │       \ /                                │
    │        *  k₇                             │
    │                                          │
    │   Query q →  finds k₅ in O(log n)        │
    │   (instead of scanning all n keys)       │
    │                                          │
    └──────────────────────────────────────────┘

    Standard KV-cache: O(t) per decoding step
    HullKVCache:       O(log t) per decoding step

    For million-step traces:
      Standard: ~260 seconds, 188 tok/s
      HullKV:   ~1.3 seconds, 31,000+ tok/s
```

### Why 2D Suffices

Memory/stack lookups require index queries: "give me the value at index i."

Store index j as key k_j = (2j, -j²). Query index i with q = (i, 1):
```
argmax_j { (2j, -j²) · (i, 1) } = argmax_j { 2ij - j² } = i
```
The quadratic penalty ensures only the exact match wins. 2D is sufficient for index lookup; cumulative sums (for instruction pointer, stack depth) only need 1D.

### Computation as Append-Only Trace

```
    EXECUTION MODEL
    ┌──────────────────────────────────────────┐
    │                                          │
    │   [Prompt: program code]                 │
    │   [Token 1: first execution step]        │
    │   [Token 2: second execution step]       │
    │   ...                                    │
    │   [Token t: current step]                │
    │     ↑                                    │
    │     Looks back at O(1) prior positions   │
    │     via attention heads to reconstruct   │
    │     current machine state:               │
    │       - instruction pointer (cumsum)     │
    │       - stack top (index lookup)          │
    │       - memory cell (index lookup)        │
    │       - call stack depth (cumsum)         │
    │                                          │
    │   Each step: ≤ 5 tokens per instruction  │
    │   No external state. No editable memory. │
    │   Just an append-only trace.             │
    │                                          │
    └──────────────────────────────────────────┘
```

### Performance

| Demo | Tokens | Speed | Time |
|------|--------|-------|------|
| Hungarian algorithm (10×10) | 114,839 | 34,576 tok/s | ~3.3s |
| Arto Inkala Sudoku | 2,270,400 | 34,585 tok/s | ~66s |
| Standard KV-cache (same trace) | same | 188 tok/s | ~260s |

The HullKVCache provides **~165x speedup** over standard KV-cache for long traces.

## Future Directions (from the post)

### 1. k-Sparse Softmax Attention
Rather than hard-max, retrieve top-k keys from nested convex hulls and apply softmax only over those. Cost: O(k + log n). Extends to 3D heads via 3D convex hulls.

### 2. Training Large Models with 2D Heads
2D heads don't limit total model size — use more heads and more layers to match parameter budgets. Deployment modes:
- **Fast path:** Dedicated executor for heavy computation
- **Fast/slow hybrid:** 2D heads execute, full-dim heads reason
- **Speculative decoding:** 2D model proposes, large model verifies

### 3. Programs Compiled into Weights ⭐
> "In principle, arbitrary programs can be compiled directly into the transformer weights, bypassing the need to represent them as token sequences at all. That would make weights themselves a deployment target for software."

This is the most directly relevant future direction. The post explicitly describes:
```
C SOURCE CODE → [compile] → TRANSFORMER WEIGHTS (W_Q, W_K, W_V, W_O, W_ff)
```

### 4. Training Beyond Gradient Descent
> "If logic can be compiled into weights, then gradient descent is no longer the only way to modify a model. Weight compilation provides another route for inserting structure, algorithms, and guarantees directly into a network."

### 5. Growing AI Systems Like Software
> "If software becomes part of the neural architecture, then AI systems need a way to grow over time much like software libraries do today."

The vision: modules of compiled program logic, added incrementally to the model's internal execution engine.

## Relevance to Compiled Verification

### This paper IS the core of the thesis

Percepta's work establishes Tier 3 of the four-tier argument: **the forward pass itself can be computation.** Key connections:

| Percepta Capability | Compiled Verification Extension |
|---------------------|--------------------------------|
| WebAssembly interpreter in weights | Rubric checker in weights |
| C → WASM → tokens → execution | Rubric → checker spec → compiled weights |
| O(log t) decoding | Efficient validation of long outputs |
| Programs compiled into weights (future) | Rubric compiled into validator weights |
| Standard transformer architecture | Works with existing model infrastructure |
| Growing AI like software | Adding new validation capabilities incrementally |

### The Gap

Percepta currently compiles an **interpreter** into weights, then feeds it programs as tokens. The compiled-verification thesis requires the **program itself** (the rubric checker) to be compiled into weights. Percepta explicitly identifies this as a future direction.

### Why This Matters for Agent Validation

If you can compile a rubric checker into transformer weights:
1. **Deterministic:** The check is executed by fixed weights, not stochastic generation
2. **Efficient:** O(log t) attention means validation scales sublinearly
3. **Integrated:** The validator runs inside the model's own forward pass
4. **Auditable:** The execution trace is fully visible in the output stream
5. **Compositional:** New validators can be added like software modules

## Open Questions

- Can the weight compilation go beyond interpreters to arbitrary programs?
- What's the expressiveness ceiling of 2D attention heads for program execution?
- How would you compile a natural-language rubric into WASM, then into weights?
- Can the model learn *when* to invoke the fast execution path vs. normal generation?
- What formal guarantees can be provided about compiled-weight execution correctness?

## Citation

```bibtex
@misc{tzamos2026llms,
  title={Can LLMs Be Computers?},
  author={Tzamos, Christos and {Percepta Team}},
  howpublished={Percepta Field Notes},
  url={https://www.percepta.ai/blog/can-llms-be-computers},
  year={2026},
  month={March}
}
```

## Review Status

- [x] Read full blog post via browser tool (JS-rendered)
- [x] Extracted architecture details (d_model=36, n_heads=18, head_dim=2, 7 layers)
- [x] Understood HullKVCache mechanism (2D convex hull queries)
- [x] Mapped all future directions (k-sparse, programs into weights, growing AI)
- [x] Connected to all four tiers of the compiled-verification argument
