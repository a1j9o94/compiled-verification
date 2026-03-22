# Synthesis: Hypernetworks, In-Model Computation, and Compiled Verification

**Date:** March 22, 2026
**Purpose:** Technical foundation for the compiled-verification thesis in Adrian's Substack article on AI agent validation.

---

## The Four-Tier Argument

The article argues a progression from stochastic validation to compiled verification:

```
Tier 1: LLM-as-Judge          — probabilistic, insufficient
Tier 2: Tool Calling           — deterministic ops, stochastic orchestration  
Tier 3: In-Model Computation   — forward pass IS computation (Percepta)
Tier 4: Compiled Verification  — forward pass COMPILES deterministic validator
```

This synthesis evaluates whether the literature supports this argument.

---

## 1. Is the Four-Tier Argument Technically Sound?

**Yes, with caveats.** Each tier is supported by existing work:

### Tier 1 → Tier 2 (Well-established)
The limitation of LLM-as-judge is widely documented. Tool calling (function calling, code interpreters) is the standard remedy. The observation that "the operation is deterministic but the orchestration is stochastic" is correct and well-supported.

### Tier 2 → Tier 3 (Demonstrated by Percepta)
Percepta (Tzamos, 2026) concretely demonstrates that a standard transformer can execute programs internally via its forward pass. Their WebAssembly interpreter in weights, combined with O(log t) HullKVCache decoding, makes this practical at scale (34k tok/s, millions of steps). This is not just theoretical — they solve the hardest known Sudoku entirely within the model.

**Supporting theoretical foundations:**
- Giannou et al. (2023): Proved a 13-layer looped transformer can emulate a general-purpose computer
- Schlag et al. (2021): Showed that linear transformers are literally Fast Weight Programmers — the forward pass modifies weights at each step
- Dai et al. (2022): Demonstrated that in-context learning implicitly performs gradient descent, meaning the forward pass already "adjusts" the model's effective behavior

### Tier 3 → Tier 4 (Theoretically grounded but not yet demonstrated)
The jump from "forward pass executes programs" to "forward pass compiles rubric → validator weights" is the novel claim. The literature supports its plausibility:

| What's needed | What exists |
|---------------|-------------|
| Compile algorithm → weights | Tracr (Lindner et al., 2023): RASP → transformer weights |
| One network generates another's weights | HyperNetworks (Ha et al., 2016) |
| Generated weights implement algorithms | Liao et al. (2023): Hypernetworks discover 3 algorithms |
| Forward pass modifies weights | Fast Weight Programmers (Schlag et al., 2021) |
| Weights grow incrementally like software | Continual learning via hypernetworks (von Oswald et al., 2020) |

**The gap:** No one has demonstrated the full pipeline: natural-language rubric → compiled validator weights → deterministic checking. Each component exists in isolation.

**Assessment: The argument is technically sound as a research direction. It's a conjecture extrapolated from concrete capabilities, not a proven result.**

---

## 2. Is Tracr the Closest Existing Work to "Compile Rubric → Deterministic Validator"?

**Yes. Tracr is the single most relevant paper.**

Tracr (Lindner et al., 2023) literally compiles human-readable programs into standard transformer weights. The resulting transformer executes the program exactly — not approximately. The compilation pipeline (RASP → computation graph → residual stream allocation → weight matrices) is constructive and produces standard architectures.

Tracr already compiles primitive validation operations:
- **Parenthesis checking** (structural validity)
- **Token frequency counting** (attribute verification)
- **Sorting** (ordering constraints)

These are building blocks of rubric checking.

### What Tracr Lacks for Full Compiled Verification

```
    THE FULL PIPELINE (not yet built)
    ┌──────────────────────────────────────────────────────┐
    │                                                      │
    │   1. Natural language rubric                          │
    │      "Ensure the response cites at least 3 sources,  │
    │       uses formal tone, and stays under 500 words"   │
    │              │                                       │
    │              ↓  [GAP 1: NL → Formal spec]            │
    │   2. Formal specification (RASP or similar)           │
    │      count_sources ≥ 3 AND                           │
    │      formality_score > 0.8 AND                       │
    │      word_count < 500                                │
    │              │                                       │
    │              ↓  [Tracr can do this part]              │
    │   3. Transformer weights                              │
    │      W_Q, W_K, W_V, W_O, W_ff                       │
    │              │                                       │
    │              ↓  [Standard inference]                  │
    │   4. Deterministic validation result                  │
    │      PASS / FAIL with trace                          │
    │                                                      │
    └──────────────────────────────────────────────────────┘
    
    Gap 1 is the hard part.
    Tracr solves step 2→3.
    Percepta's HullKVCache solves step 3→4 efficiently.
```

### Runner-up: Percepta's "Programs into Weights" Vision

Percepta explicitly describes compiling C source code directly into transformer weights as a future direction. If realized, this would subsume Tracr's approach with a more practical compilation target (C/WASM vs RASP). But this is currently a vision, not a demonstrated capability.

### Comparison Table

| Paper | What it compiles | Target | Exact? | Demonstrated? |
|-------|-----------------|--------|--------|---------------|
| **Tracr (Lindner 2023)** | RASP programs | Transformer weights | **Yes** | **Yes** |
| Percepta (Tzamos 2026) | WASM interpreter | Transformer weights | Yes | Yes (interpreter only) |
| Giannou et al. (2023) | Instruction set | Transformer weights | Yes | Yes (constructive proof) |
| Liao et al. (2023) | L1 norm algorithms | MLP weights | ~Yes | Yes (hypernetwork discovers them) |
| Ha et al. (2016) | Layer descriptions | Layer weights | No (statistical) | Yes |

---

## 3. What's the Gap Between Current Capability and "Compile NL Rubric → Deterministic Checker"?

The gap has three components:

### Gap A: Natural Language → Formal Specification
**Difficulty: Very Hard**

No existing system can reliably convert natural language rubrics into formal, unambiguous specifications. This is essentially the requirements engineering problem in software engineering — one of the hardest problems in CS.

Possible approaches:
- LLM-assisted formalization (use a large model to generate RASP/formal specs from NL)
- Interactive specification (human-in-the-loop disambiguation)
- Template-based rubrics (restrict NL to a formal template language)

### Gap B: Scalability of Compilation
**Difficulty: Hard**

Tracr's compilation scales poorly:
- Residual stream width grows linearly with the number of variables
- Transformer depth grows linearly with program depth
- No support for iteration (all programs must be finite-depth)

For practical rubric checking, we'd need:
- Compiled validators for checking operations that compose
- Efficient residual stream sharing (via superposition?)
- Iteration support (via looping, cf. Giannou et al.)

### Gap C: Semantic Checking vs Syntactic Checking
**Difficulty: Currently Impossible**

Tracr-style compilation works for **syntactic** checks (structure, counts, patterns). Many rubric criteria are **semantic** (quality, relevance, tone). A fully compiled approach may only handle the syntactic subset, requiring a hybrid:

```
    HYBRID VALIDATION ARCHITECTURE
    ┌──────────────────────────────────────────┐
    │                                          │
    │   Input: Agent output to validate         │
    │                                          │
    │   ┌────────────────────┐                 │
    │   │ Compiled validator  │ ← Deterministic │
    │   │ (structural checks) │   (Tracr-style) │
    │   └────────────────────┘                 │
    │         │                                │
    │         ↓ If structural checks pass:     │
    │                                          │
    │   ┌────────────────────┐                 │
    │   │ Neural validator    │ ← Stochastic   │
    │   │ (semantic checks)   │   (LLM-based)  │
    │   └────────────────────┘                 │
    │         │                                │
    │         ↓                                │
    │   Combined verdict                       │
    │                                          │
    └──────────────────────────────────────────┘
```

---

## 4. Does the Fast Weight / Schmidhuber Lineage Count as "Forward Pass Compiles Weights"?

### The Precise Claim

**Yes, but in a specific, limited sense.**

The Schmidhuber (1991-1993) / Schlag et al. (2021) Fast Weight Programmer lineage demonstrates:

1. **The forward pass genuinely modifies weights:** The fast weight matrix W(i) is updated at every timestep via outer-product programming instructions.

2. **The modifications are learned:** The slow network learns *what* modifications to make — it learns a programming language over fast weights.

3. **The modifications constitute computation:** The accumulated fast weights perform associative retrieval, a form of computation.

4. **The modifications happen during inference:** No gradient-based training is involved; the fast weight updates occur in the forward pass.

### What It IS:
- Forward pass writes key-value associations into a fast weight memory
- The slow network has learned to program this memory effectively
- Each attention step is a "programming instruction" modifying the fast weights
- This is literally "inference-time weight modification by the forward pass"

### What It ISN'T:
- The "programs" are limited to linear associative memory (no conditional logic, no iteration)
- The fast weights don't implement arbitrary algorithms — just key-value lookup
- The capacity is bounded by the key dimension
- There's no "compilation" of a specification — the behavior emerges from training

### The Schmidhuber Lineage as Proto-Compilation

The progression from FWPs to compiled verification:

```
1991: Schmidhuber's FWPs        → Forward pass programs fast weights
                                   (limited to outer-product memory)

2021: Schlag et al. (FWP=LT)    → Same thing, shown equivalent to attention
                                   (with delta rule for better programming)

2022: Dai et al. (ICL=GD)       → In-context learning as implicit finetuning
                                   (entire model behaves as if weights changed)

2023: Tracr (Lindner et al.)     → Algorithms explicitly compiled to weights
                                   (constructive, exact, but offline)

2023: Giannou et al.             → Looped transformers = universal computers
                                   (any program in weights, constructively)

2026: Percepta (Tzamos)          → Programs executed inside transformer
                                   (practical, fast, WebAssembly in weights)

????  COMPILED VERIFICATION      → Rubric compiled to deterministic checker
                                   (forward pass generates validator weights)
```

**The FWP lineage is the conceptual ancestor, but compiled verification requires going far beyond what FWPs currently demonstrate.**

---

## 5. Top Open Research Questions

### Q1: Can natural language be compiled to RASP (or equivalent)?
**Impact: Critical.** This is the bottleneck for the full pipeline. An LLM that can translate rubric criteria into RASP programs would close the most important gap. Even a restricted rubric language (not free-form NL) that maps cleanly to RASP would be a major advance.

### Q2: Can Tracr-style compilation and Percepta's HullKVCache be combined?
**Impact: High.** Tracr compiles programs into standard transformer weights. Percepta's 2D attention heads enable O(log t) execution. If compiled validators use 2D heads, they'd inherit the efficiency benefits — making compiled verification practical for long outputs.

### Q3: Can a hypernetwork learn to compile?
**Impact: Transformative.** Rather than hand-crafting a compiler (Tracr), train a hypernetwork that takes a specification (rubric embedding) and generates validator weights. This combines:
- Ha et al.'s hypernetwork architecture (one net generates another's weights)
- Von Oswald et al.'s task conditioning (specification → weights)
- Liao et al.'s algorithm discovery (the hypernetwork finds efficient implementations)
- Tracr's exactness guarantee (compiled validators must be correct)

This is the most promising research direction for compiled verification.

### Q4: What is the computational class of 2D-attention-compiled programs?
**Impact: Foundational.** Percepta uses 2D attention heads. Tracr uses full attention. Giannou et al. prove universality for standard transformers. What can a 2D-head transformer compute? Is it Turing-complete with looping? Understanding this determines whether compiled validators with efficient decoding can express arbitrary checking logic.

### Q5: Can formal verification be applied to compiled transformer weights?
**Impact: High for safety.** If you compile a rubric into weights, can you *prove* the weights correctly implement the rubric? This would close the loop: the validator is not just deterministic but provably correct. Tracr's known-structure models are a starting point — the weights have known semantics by construction.

---

## Summary Table: All Papers and Their Roles

| Paper | Year | Role in Thesis | Key Contribution |
|-------|------|----------------|------------------|
| HyperNetworks (Ha) | 2016 | Foundation | One network generates another's weights |
| CL with Hypernetworks (von Oswald) | 2020 | Extension | Task-conditioned, compressive, incremental |
| FWP = Linear Transformers (Schlag) | 2021 | Mechanism | Forward pass modifies weights (delta rule) |
| ICL as Gradient Descent (Dai) | 2022 | Context | ICL ≈ implicit weight compilation |
| Looped Transformers (Giannou) | 2023 | Theory | Constructive proof: programs in weights |
| Tracr (Lindner) | 2023 | **Core** | **Algorithm → transformer weights (exact)** |
| Interpretable Hypernetworks (Liao) | 2023 | Evidence | Hypernetworks discover novel algorithms |
| Percepta (Tzamos) | 2026 | **Core** | **Forward pass = computation (practical)** |

---

## Conclusion

The compiled-verification thesis — that a forward pass can compile a natural-language rubric into a small deterministic validator — is **technically plausible but not yet demonstrated.** The individual components exist:

1. **Tracr** proves that algorithms can be compiled into transformer weights (exactly).
2. **Percepta** proves that transformers can execute programs efficiently in their own forward pass.
3. **Hypernetworks** prove that one network can generate another's weights from a specification.
4. **Fast Weight Programmers** prove that the forward pass can modify weights during inference.

The unsolved challenge is **composition**: combining these capabilities into a system where an LLM reads a natural-language rubric, generates a formal specification, compiles it into transformer weights, and runs those weights as a deterministic checker. The hardest gap is step 1 (NL → formal spec); the remaining steps have concrete technical paths.

For the Substack article, the four-tier framing is **sound and well-supported by literature.** The jump from Tier 3 to Tier 4 is speculative but grounded in real capabilities. Framing it as an open research direction rather than a solved problem would be both accurate and compelling.

---

*This synthesis covers 8 papers across two research areas (hypernetworks and in-model computation) and evaluates their collective support for the compiled-verification thesis.*
