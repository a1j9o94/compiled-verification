# Tracr: Compiled Transformers as a Laboratory for Interpretability

**Authors:** David Lindner, János Kramár, Sebastian Farquhar, Matthew Rahtz, Thomas McGrath, Rohin Shah
**Year:** 2023
**Venue:** NeurIPS 2023 (Spotlight) / arXiv:2301.05062
**Links:** [Paper](https://arxiv.org/abs/2301.05062) | [Code](https://github.com/google-deepmind/tracr)

## Summary

Tracr is a **compiler** from human-readable programs to standard decoder-only transformer weights. Given a program written in RASP (Restricted Access Sequence Processing Language), Tracr produces a transformer model with **known, deterministic structure** — the weights implement exactly the specified program, not a statistical approximation.

This is literally "compile an algorithm into transformer weights." The resulting models are used as ground truth for evaluating interpretability methods, but the compilation machinery itself is the breakthrough: it demonstrates that the mapping from algorithm → transformer weights is possible, constructive, and produces standard architectures.

## Key Technical Insights

### The RASP Language

RASP (Weiss et al., 2021) is a programming language designed to express computations that transformers can perform. It has two core primitives:

1. **select(keys, queries, predicate):** Creates an attention pattern — a binary matrix where position (i,j) = 1 iff predicate(keys[i], queries[j]) is true.

2. **aggregate(selector, values):** Applies the attention pattern to aggregate values — computes a weighted average (or sum) of values according to the selector.

RASP programs compose these primitives with elementwise operations (map) to express algorithms.

### The Compilation Pipeline

```
    TRACR COMPILATION PIPELINE
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   RASP Program (human-readable)                       │
    │     │                                                │
    │     ↓                                                │
    │   [1. RASP → Computation Graph]                       │
    │     Parse RASP into a directed acyclic graph          │
    │     of select/aggregate/map operations                │
    │     │                                                │
    │     ↓                                                │
    │   [2. Graph → Residual Stream Allocation]             │
    │     Assign each intermediate variable to              │
    │     a subspace of the residual stream.                │
    │     Variables get orthogonal subspaces.               │
    │     │                                                │
    │     ↓                                                │
    │   [3. Operations → Attention Heads + MLPs]            │
    │     select/aggregate → attention head weights         │
    │     map operations → MLP weights                     │
    │     Each RASP operation → one transformer layer       │
    │     │                                                │
    │     ↓                                                │
    │   [4. Assembly → Standard Transformer]                │
    │     Combine all layers into a standard                │
    │     decoder-only transformer.                         │
    │     W_Q, W_K, W_V, W_O, W_ff all specified.         │
    │                                                      │
    │   OUTPUT: A standard transformer that EXACTLY          │
    │   implements the RASP program.                        │
    │                                                      │
    └──────────────────────────────────────────────────────┘
```

### Compilation Details

**Residual stream allocation:** Each RASP variable gets its own orthogonal subspace in the residual stream. This prevents interference between variables — the model dimension grows with the number of variables. This is a key limitation: the residual stream must be large enough to hold all intermediate values.

**Attention pattern compilation:**
- A RASP `select(keys, queries, predicate)` becomes attention weights W_Q and W_K such that the resulting attention pattern matches the predicate.
- For equality predicates: W_Q and W_K project to the subspaces of keys and queries, producing high attention when they match.

**MLP compilation:**
- Elementwise operations (map) become MLP layers.
- The MLP reads from the appropriate residual stream subspace and writes to the output subspace.

### Compiled Programs

The paper demonstrates compilation of:

1. **Token frequencies:** Count how often each token appears in the sequence
2. **Sorting:** Sort a sequence of tokens
3. **Parenthesis checking:** Determine if parentheses are balanced (Dyck language recognition)

### Superposition Investigation

The paper uses Tracr models to study **superposition** — the phenomenon where neural networks represent more features than they have dimensions. By compiling a known program and then compressing the residual stream, they can observe exactly when and how superposition occurs, with ground truth for comparison.

## Architecture of Compiled Models

```
    COMPILED TRANSFORMER STRUCTURE
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   Residual stream: d_model = Σ dim(variable_i)       │
    │   (one orthogonal subspace per RASP variable)        │
    │                                                      │
    │   Layer 1: select_1/aggregate_1                       │
    │     ┌─────────┐                                      │
    │     │ Attn    │ ← W_Q, W_K implement select_1       │
    │     │ Head 1  │ ← W_V, W_O implement aggregate_1    │
    │     └─────────┘                                      │
    │         │                                            │
    │     ┌─────────┐                                      │
    │     │ MLP 1   │ ← Implements map operations          │
    │     └─────────┘   between layers 0 and 1             │
    │         │                                            │
    │   Layer 2: select_2/aggregate_2                       │
    │     ┌─────────┐                                      │
    │     │ Attn    │ ← Implements second attention op     │
    │     │ Head 2  │                                      │
    │     └─────────┘                                      │
    │     ...                                              │
    │                                                      │
    │   Output: Read from the output variable's subspace   │
    │                                                      │
    │   GUARANTEE: The transformer computes EXACTLY the     │
    │   RASP program. Not an approximation.                │
    │                                                      │
    └──────────────────────────────────────────────────────┘
```

## Relevance to Compiled Verification

### This is the MOST directly relevant paper

Tracr is literally "compile an algorithm into transformer weights." The compiled-verification thesis asks whether this can be extended from simple algorithms to rubric checkers.

| Tracr | Compiled Verification |
|-------|----------------------|
| RASP program → transformer weights | Rubric checker → validator weights |
| Parenthesis checking compiled | Could check structural properties |
| Token frequency compiled | Could count/verify attributes |
| Sorting compiled | Could verify ordering constraints |
| Exact (not approximate) | Deterministic validation required |
| Standard decoder-only transformer | Standard architecture |

### What Tracr Can Already Do

Tracr already compiles programs that are primitive verification tasks:
- **Parenthesis checking** = structural validity checking
- **Token frequency** = counting-based validation
- **Sorting** = ordering verification

These are simple rubric components. A "compiled rubric checker" would compose such primitives.

### The Gap: RASP vs Natural Language

Tracr compiles RASP programs, not natural language. The full compiled-verification pipeline would be:

```
Natural language rubric
    → [LLM/compiler] → RASP program
    → [Tracr] → Transformer weights
    → Deterministic validator
```

The "natural language → RASP" step is where the unsolved challenge lies.

### Scalability Limitations

1. **Residual stream grows with program complexity:** Each variable needs its own subspace. Complex programs need very wide residual streams.
2. **One RASP operation per layer:** Program depth = transformer depth. Complex programs need deep transformers.
3. **RASP is limited:** Not all algorithms are naturally expressible in select/aggregate form. RASP captures a specific (though interesting) computational class.
4. **No loops:** RASP programs are non-iterative. For iterative checking, you'd need to combine Tracr with looping (cf. Giannou et al. 2023).

### The Compilation Analogy

Tracr is to transformers what a compiler is to CPUs:

```
C code   → [gcc]  → x86 machine code → Runs on CPU
RASP code → [Tracr] → Transformer weights → Runs on transformer
```

The compiled-verification thesis extends this:
```
Rubric → [Rubric compiler] → Transformer weights → Validates outputs
```

## Open Questions

- Can RASP (or an extension) express the kind of checks needed for AI agent validation?
- Can the residual stream allocation be compressed (via superposition) without losing correctness?
- Can Tracr be extended to handle iterative/looping programs?
- What happens when you compose many compiled primitives — does the model become impractically large?
- Can you train a neural compiler that maps natural language → RASP → weights end-to-end?
- Can compiled verification be formally verified (proof that the weights correctly implement the rubric)?

## Citation

```bibtex
@inproceedings{lindner2023tracr,
  title={Tracr: Compiled Transformers as a Laboratory for Interpretability},
  author={Lindner, David and Kram{\'a}r, J{\'a}nos and Farquhar, Sebastian and Rahtz, Matthew and McGrath, Thomas and Shah, Rohin},
  booktitle={Advances in Neural Information Processing Systems},
  volume={36},
  year={2023}
}
```

## Review Status

- [x] Read abstract and key results
- [x] Analyzed compilation pipeline (RASP → graph → residual stream → weights)
- [x] Identified compiled programs (frequencies, sorting, parentheses)
- [x] Connected to compiled-verification thesis as most directly relevant paper
- [x] Mapped the gap: RASP expressiveness vs. rubric checking requirements
- [x] Noted scalability limitations (residual stream width, depth)
