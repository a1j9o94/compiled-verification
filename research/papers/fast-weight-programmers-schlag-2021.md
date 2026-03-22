# Linear Transformers Are Secretly Fast Weight Programmers

**Authors:** Imanol Schlag, Kazuki Irie, Jürgen Schmidhuber
**Year:** 2021
**Venue:** ICML 2021 / arXiv:2102.11174
**Links:** [Paper](https://arxiv.org/abs/2102.11174) | [Code](https://github.com/ischlag/fast-weight-transformers)

## Summary

This paper reveals a profound formal equivalence: **linearized self-attention mechanisms are identical to Fast Weight Programmers (FWPs) from Schmidhuber's work in the early 1990s.** In FWPs, a "slow" network learns by gradient descent to program the "fast weights" of another network through sequences of elementary programming instructions — specifically, additive outer products of self-invented key and value patterns.

The paper shows that linear Transformers are precisely this: each attention step writes a key-value association into a fast weight matrix via an outer product, and retrieval is a matrix-vector multiplication with the query. The fast weight matrix **changes at every timestep during inference** — making this the closest existing mechanism to "the forward pass compiles weights."

Beyond establishing the equivalence, the authors improve the FWP programming instruction from purely additive outer products to a **delta rule** that can correct and overwrite previous associations, with learned dynamic learning rates.

## Key Technical Insights

### The Core Equivalence

Standard self-attention (without softmax) at step i:

```
y(i) = W(i) · q(i)

where W(i) = Σ_{j=1}^{i} v(j) ⊗ k(j)    (outer product accumulation)
```

This IS a Fast Weight Programmer:
- **Slow weights:** W_k, W_v, W_q (learned by gradient descent during training)
- **Fast weights:** W(i) (updated at every timestep during inference)
- **Programming instruction:** v(j) ⊗ k(j) (outer product of value and key)
- **Retrieval:** W(i) · q(i) (matrix-vector multiplication)

The slow network learns to *invent* keys and values that, when combined via outer products, program a useful fast weight memory.

### Memory Capacity Limitation

The fast weight matrix W(i) ∈ ℝ^{d_value × d_dot}. For interference-free retrieval, keys must be orthogonal. Maximum orthogonal keys in d_dot dimensions = d_dot. Therefore:

**When sequence length L > d_dot, the model enters overcapacity regime** — new associations interfere with old ones.

This is a fundamental limitation of linear attention / FWPs, and motivates the delta rule improvement.

### The Delta Rule Improvement

Instead of purely additive updates, the improved instruction:

```
v̄(i) = W(i-1) · φ(k(i))          # Retrieve current value for this key
β(i)  = σ(W_β · x(i))              # Learned dynamic "learning rate"
v_new = β(i)·v(i) + (1-β(i))·v̄(i) # Interpolate old and new

W(i) = W(i-1) + v_new ⊗ φ(k(i))   # Write new
              - v̄(i) ⊗ φ(k(i))     # Remove old
```

This is exactly the Widrow-Hoff delta rule, but with:
- Self-invented keys and values (not pre-specified)
- Dynamically computed learning rate β
- End-to-end differentiable training

## Architecture

```
              FAST WEIGHT PROGRAMMER (= Linear Transformer)
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   SLOW WEIGHTS (trained by gradient descent):            │
    │     W_k, W_v, W_q, W_β                                  │
    │                                                         │
    │   At each timestep i:                                    │
    │                                                         │
    │   x(i) ──→ [W_k] ──→ k(i) ──→ φ(k(i))                 │
    │        ──→ [W_v] ──→ v(i)                               │
    │        ──→ [W_q] ──→ q(i) ──→ φ(q(i))                  │
    │        ──→ [W_β] ──→ β(i) (dynamic learning rate)       │
    │                                                         │
    │   FAST WEIGHT MEMORY W(i):                               │
    │                                                         │
    │   ┌──────────────────────────────┐                      │
    │   │  1. Retrieve: v̄ = W(i-1)·φ(k) │  (read old value)  │
    │   │  2. Compute delta:             │                    │
    │   │     Δ = β(v - v̄)              │  (error signal)    │
    │   │  3. Update: W(i) = W(i-1)     │                    │
    │   │           + Δ ⊗ φ(k)          │  (delta rule)      │
    │   └──────────────────────────────┘                      │
    │                                                         │
    │   Output: y(i) = W(i) · φ(q(i))                         │
    │                 / (z(i) · φ(q(i)))   (normalized)       │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

    Key insight: W(i) is MODIFIED AT EVERY TIMESTEP during inference.
    The "slow" network learns HOW to modify it.
    The "fast" weights ARE the computation being performed.
```

### DPFP: Deterministic Parameter-Free Projection

The authors also propose a new kernel function φ for linearizing attention:

```
φ_{iν}(k) = r([k; -k])_i · r([k; -k])_{i+ν}

where r(a) = max(0, a) (ReLU)
      ν controls capacity (higher ν = more dimensions = more capacity)
```

This projects d_key → 2·d_key·ν dimensions deterministically, increasing memory capacity without random features.

## Results

| Task | FWP + Delta Rule | Linear Transformer | Standard Transformer |
|------|------------------|--------------------|----------------------|
| Synthetic retrieval (capacity test) | **Solves** | Fails at overcapacity | Solves |
| WMT14 EN-DE (BLEU) | 25.6 | 24.2 | 27.6 |
| Wikitext-103 (PPL) | 33.9 | 36.1 | 24.0 |

The delta rule consistently outperforms purely additive linear attention, especially under memory pressure.

## Relevance to Compiled Verification

### This is the closest existing work to "forward pass compiles weights"

The Fast Weight Programmer paradigm is precisely the mechanism the compiled-verification thesis needs:

| FWP Mechanism | Compiled Verification Analog |
|---------------|------------------------------|
| Slow weights learn to program fast weights | Training learns to compile rubrics into checker weights |
| Forward pass modifies W(i) at each step | Forward pass writes validator logic into fast weights |
| Delta rule corrects/overwrites associations | Validator can update its checking logic in-context |
| Keys = addresses, Values = stored data | Rubric criteria = addresses, checking logic = data |

### The Precise Claim

Does this constitute "weight compilation during inference"? **Yes, in a limited sense:**

1. The fast weight matrix W(i) is genuinely modified during the forward pass
2. The modifications are *programmed* by the slow network (which learned what modifications to make)
3. Each modification is an elementary "programming instruction" (outer product)
4. The accumulated fast weights perform a *computation* (associative retrieval)

**But it's limited because:**
- The "programs" are restricted to key-value associative memory
- There's no conditional logic, loops, or branching in the fast weight updates
- The fast weights are a linear map, limiting computational expressiveness
- The capacity is bounded by the key dimension

### Connection to Schmidhuber's Vision

Schmidhuber (1991, 1992, 1993) articulated the vision of "a slow network learning to program a fast network" decades before modern transformers. This paper validates that vision within the transformer framework. The compiled-verification extension asks: can we push this further, from programming an associative memory to programming a full deterministic checker?

## Open Questions

- Can the delta rule be extended to write more complex programs (not just key-value pairs) into fast weights?
- What happens if we stack FWP layers — does the composed fast-weight manipulation become Turing-complete?
- Can the slow network learn to program fast weights that implement a specific algorithm (e.g., rubric checking)?
- Is there a theoretical limit on what computations can be "programmed" into fast weights during a forward pass?
- How does the FWP view connect to in-context learning? (ICL as implicit fast-weight programming?)

## Citation

```bibtex
@inproceedings{schlag2021linear,
  title={Linear Transformers Are Secretly Fast Weight Programmers},
  author={Schlag, Imanol and Irie, Kazuki and Schmidhuber, J{\"u}rgen},
  booktitle={International Conference on Machine Learning},
  pages={9355--9366},
  year={2021},
  organization={PMLR}
}
```

## Review Status

- [x] Read full HTML paper (Sections 1-6)
- [x] Extracted core equivalence and delta rule
- [x] Connected to compiled-verification thesis
- [x] Identified as closest existing work to "forward pass compiles weights"
- [x] Mapped limitations for deterministic program generation
