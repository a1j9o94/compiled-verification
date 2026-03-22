# Generating Interpretable Networks using Hypernetworks

**Authors:** Isaac Liao, Ziming Liu, Max Tegmark
**Year:** 2023
**Venue:** arXiv:2312.03051
**Links:** [Paper](https://arxiv.org/abs/2312.03051) | [HTML](https://arxiv.org/html/2312.03051v1)

## Summary

This paper from MIT addresses whether hypernetworks can generate neural networks that implement **interpretable algorithms** — not just good-performing weights, but weights whose underlying computation can be decoded by humans. The key innovation: by controlling the complexity of generated networks (via a KL divergence penalty β), the hypernetwork produces a diverse family of networks ranked by complexity, all of which are interpretable in hindsight.

For the task of computing the L1 norm, the hypernetwork independently discovers three distinct algorithms — only one of which the authors anticipated. This demonstrates that **hypernetworks can generate weights that implement specific, identifiable algorithms**, not just statistical approximations.

## Key Technical Insights

### Three Discovered Algorithms for L1 Norm

1. **The Double-Sided Algorithm** (expected):
   ```
   ||x||₁ = Σᵢ ReLU(xᵢ) + Σᵢ ReLU(-xᵢ)
   ```
   Each hidden neuron handles either the positive or negative part of one input dimension. Requires 2n hidden neurons.

2. **The Pudding Algorithm** (unexpected):
   ```
   ||x||₁ = 2·Σⱼ ReLU(∓xⱼ ± Σᵢ xᵢ) ± Σᵢ xᵢ
   ```
   Uses global sum information plus per-element corrections. Requires only n+1 hidden neurons — **more parameter-efficient** than the double-sided approach.

3. **The Convexity Algorithm** (unexpected):
   ```
   ||x||₁ ≈ α · Σⱼ swish(Σᵢ Wᵢⱼ · xᵢ)
   ```
   Approximates the L1 norm using random projections, exploiting the convexity of the norm. Less accurate but simplest.

### Complexity Control via β

The hypernetwork uses a VAE-like structure with a complexity penalty:
- **High β:** Favors simplicity → convexity algorithm (random, simple)
- **Medium β:** Balanced → pudding algorithm (structured, efficient)
- **Low β:** Favors accuracy → double-sided algorithm (precise, interpretable)

**Phase transitions** between algorithms occur as β is swept, showing discrete algorithmic phases rather than continuous interpolation.

### Systematic Generalization

A hypernetwork trained on 16-dimensional inputs can correctly generate L1-norm networks for **input dimensions not seen during training** (including larger dimensions). This demonstrates that the hypernetwork learned a **general algorithm schema**, not just memorized weights for specific dimensions.

### Hypernetwork vs Standard Training

Networks trained by Adam are nearly uninterpretable — messy weight patterns with no clear structure. The same task solved by a hypernetwork-generated network has clean, structured weights where the algorithm is visible by inspection. The hypernetwork's complexity control acts as an **interpretability regularizer**.

## Architecture

```
           HYPERNETWORK FOR INTERPRETABLE ALGORITHM DISCOVERY
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │   Complexity control parameter β                         │
    │                                                         │
    │   [VAE-based Hypernetwork]                               │
    │     Encoder ──→ z (latent) ──→ Decoder ──→ θ            │
    │                    ↑                          │          │
    │              KL penalty · β                   │          │
    │              (controls complexity)             ↓          │
    │                                    [Target MLP: 16→48→1] │
    │                                         │                │
    │                                         ↓                │
    │                                    L1 norm output        │
    │                                                         │
    │   Sweep β from 10⁻¹² to 1:                              │
    │                                                         │
    │   β = 10⁻¹²  ──→  Double-sided algorithm (precise)      │
    │   β = 10⁻⁶   ──→  Pudding algorithm (efficient)         │
    │   β = 1       ──→  Convexity algorithm (simple)          │
    │                                                         │
    │   PHASE TRANSITIONS between algorithms as β varies!      │
    │                                                         │
    └─────────────────────────────────────────────────────────┘

    Key insight: The hypernetwork explores the FULL SPACE
    of algorithms, not just the one gradient descent finds.
```

## Relevance to Compiled Verification

### This is the strongest evidence for "hypernetwork generates algorithmic weights"

This paper directly addresses the central question: **Can a hypernetwork generate weights that implement a specific algorithm?** The answer is yes, with caveats:

| Liao et al. Finding | Compiled Verification Implication |
|----------------------|-----------------------------------|
| Hypernetwork generates 3 distinct algorithms | A rubric-compiler could discover multiple verification strategies |
| Complexity control selects algorithm | Complexity budget constrains validator architecture |
| Pudding algorithm is more efficient | Compilation can find non-obvious efficient implementations |
| Systematic generalization across dimensions | Compiled validators could generalize across rubric variants |
| Phase transitions between algorithms | There may be discrete "modes" of verification |

### Critical Insight: Algorithm Discovery, Not Just Implementation

The hypernetwork doesn't just implement known algorithms — it **discovers novel ones** (the pudding algorithm). For compiled verification, this suggests that a rubric-to-weights compiler might discover checking strategies that humans wouldn't design.

### Limitation
The algorithms discovered are for a very simple task (L1 norm). The gap between "generate weights for L1 norm" and "generate weights for natural-language rubric checking" is enormous. The paper's networks are 2-layer MLPs with 48 hidden neurons — orders of magnitude simpler than what rubric checking would require.

## Open Questions

- Can this approach scale to more complex algorithmic tasks (sorting, graph algorithms, logical inference)?
- How does the algorithm discovery capability change with target network depth and width?
- Can the complexity-control mechanism be used to enforce formal properties (e.g., soundness, completeness) rather than just simplicity?
- Is there a systematic way to go from "generate interpretable algorithm" to "generate provably correct algorithm"?

## Citation

```bibtex
@article{liao2023generating,
  title={Generating Interpretable Networks using Hypernetworks},
  author={Liao, Isaac and Liu, Ziming and Tegmark, Max},
  journal={arXiv preprint arXiv:2312.03051},
  year={2023}
}
```

## Review Status

- [x] Read full HTML paper
- [x] Extracted three discovered algorithms (double-sided, pudding, convexity)
- [x] Analyzed phase transition behavior
- [x] Connected to compiled-verification thesis
- [x] Identified as strongest evidence for hypernetwork → algorithmic weights
