# Looped Transformers as Programmable Computers

**Authors:** Angeliki Giannou, Shashank Rajput, Jy-yong Sohn, Kangwook Lee, Jason D. Lee, Dimitris Papailiopoulos
**Year:** 2023
**Venue:** ICML 2023 / arXiv:2301.13196
**Links:** [Paper](https://arxiv.org/abs/2301.13196) | [PDF](https://proceedings.mlr.press/v202/giannou23a/giannou23a.pdf)

## Summary

This paper proves that a **constant-depth transformer placed in a loop** can emulate a general-purpose computer. The input sequence acts as a "punchcard" — containing both instructions and data. With only 13 layers and weight-sharing across loop iterations, the transformer can execute arbitrary programs including arithmetic, linear algebra, and even in-context learning algorithms that use backpropagation.

The key insight: looping a shallow transformer is equivalent to adding computational depth without adding parameters. Each loop iteration is one "clock cycle" of the virtual computer, and the input/scratchpad sequence is the "memory tape."

## Key Technical Insights

### Computational Building Blocks

The authors show that a small number of encoder layers can emulate:

1. **Embedding edit operations:** Read/write to specific positions in the sequence
2. **Non-linear functions:** ReLU, conditional selection, comparisons
3. **Function calls:** Subroutine invocation and return
4. **Program counter:** Track which instruction to execute next
5. **Conditional branches:** If-then-else based on computed values

### The Instruction Set Computer

```
    LOOPED TRANSFORMER AS A COMPUTER
    ┌──────────────────────────────────────────────┐
    │                                              │
    │   INPUT SEQUENCE (punchcard):                 │
    │   ┌──────────────────────────────────┐       │
    │   │ [INSTR₁][INSTR₂]...[INSTRₙ]     │       │
    │   │ [DATA₁][DATA₂]...[DATAₘ]        │       │
    │   │ [SCRATCH₁][SCRATCH₂]...          │       │
    │   │ [PC] [STATUS] [STACK_PTR]        │       │
    │   └──────────────────────────────────┘       │
    │                     │                         │
    │                     ↓                         │
    │            ┌─────────────────┐                │
    │     ┌──→  │  13-layer        │  ──┐           │
    │     │     │  Transformer     │    │           │
    │     │     │  (≤13 layers)    │    │           │
    │     │     └─────────────────┘    │           │
    │     │              │              │           │
    │     │              ↓              │           │
    │     │     [Modified sequence]     │           │
    │     │     (updated data +         │           │
    │     │      incremented PC)        │           │
    │     │              │              │           │
    │     └──────────────┘  (LOOP)     │           │
    │                                   │           │
    │   Each loop = one instruction     │           │
    │   cycle of the virtual computer   │           │
    │                                              │
    └──────────────────────────────────────────────┘
```

### Main Theorem

**Theorem 1 (Informal):** There exists a looped transformer with fewer than 13 layers that can emulate a basic instruction-set computer. Specifically, it can execute:
- A basic calculator (arithmetic operations)
- A basic linear algebra library (matrix operations)
- In-context learning via backpropagation

The exact weight matrices for all models are provided constructively.

### How It Works

The transformer uses the attention mechanism for:
- **Instruction fetch:** Attention to the instruction at the current PC position
- **Operand fetch:** Attention to data positions specified by the instruction
- **Write-back:** FFN layers modify the appropriate sequence positions

The program counter is stored as a special token in the sequence, incremented after each instruction. Conditional branches modify the PC based on computed flags.

### Constructive Proofs

Unlike pure existence proofs, the authors provide **explicit weight matrices**. For each computational primitive, they construct specific attention patterns and FFN weights that implement it. This makes the result concrete rather than merely theoretical.

## Relevance to Compiled Verification

### Direct Relevance: Programs in Weights (Constructively)

This paper demonstrates that specific computations can be **encoded constructively into transformer weights**. The construction is manual but exact:

| Looped Transformers | Compiled Verification |
|---------------------|----------------------|
| Instruction set encoded in weights | Validation rules encoded in weights |
| Input sequence = program + data | Input = output to validate + rubric |
| Loop = execution cycle | Loop = validation steps |
| 13 layers sufficient for universality | Small validator sufficient for checking |
| Constructive weight matrices | Weights compiled from rubric |

### Key Insight: Looping vs Depth

Standard transformers compute in O(L) depth (layers). Looped transformers trade depth for iteration count — unbounded computation from bounded depth. For validation:
- A rubric checker might need many steps (deep reasoning)
- A looped validator with compiled weights can iterate until done
- The loop count is the computational budget

### Limitation for Compiled Verification

The programs are specified as sequences of tokens in the input — the transformer reads and executes them. This is an **interpreter** model, like Percepta. The weights implement the instruction set, not the specific program. For compiled verification, we need the **specific program** (the rubric checker) in the weights, not a general interpreter.

However, the constructive proofs show it's *possible* to encode specific computations directly in weights — the theoretical foundation is solid.

### Comparison to Percepta

| Aspect | Giannou et al. 2023 | Percepta 2026 |
|--------|---------------------|---------------|
| Architecture | Encoder, looped | Decoder, autoregressive |
| Program location | In input tokens | In input tokens (WASM) |
| Computation model | RISC-like instruction set | WebAssembly VM |
| Efficiency | Not addressed (theoretical) | O(log t) via HullKVCache |
| Implementation | Constructive proofs | Working system, 34k tok/s |
| Weight construction | Manual | Trained |

## Open Questions

- Can the constructive weight matrices be learned instead of manually specified?
- How does the loop count relate to program complexity classes?
- Can the 13-layer bound be reduced while maintaining universality?
- What's the overhead of the transformer "instruction set" vs a real processor?
- Can a compiler automate the construction of weights for specific programs?

## Citation

```bibtex
@inproceedings{giannou2023looped,
  title={Looped Transformers as Programmable Computers},
  author={Giannou, Angeliki and Rajput, Shashank and Sohn, Jy-yong and Lee, Kangwook and Lee, Jason D. and Papailiopoulos, Dimitris},
  booktitle={International Conference on Machine Learning},
  pages={11398--11442},
  year={2023},
  organization={PMLR}
}
```

## Review Status

- [x] Read abstract and key results
- [x] Understood the instruction-set computer construction
- [x] Analyzed relationship to Percepta (interpreter vs compiler)
- [x] Identified as theoretical foundation for "computation in weights"
- [x] Noted constructive (not just existence) proof approach
