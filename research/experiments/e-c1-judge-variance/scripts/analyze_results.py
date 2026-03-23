#!/usr/bin/env python3
"""
E-C1: Analyze judge variance results.

Produces:
- Inter-judge agreement by criterion type and condition
- Intra-judge self-consistency
- Accuracy vs ground truth
- ANOVA for syntactic vs semantic variance
- Key numbers for the article
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np
from scipy.stats import kruskal

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
GROUND_TRUTH_FILE = PROJECT_ROOT / "data" / "ground-truth" / "ground-truth.json"
FINDINGS_FILE = PROJECT_ROOT / "FINDINGS.md"


def load_data():
    """Load summary.tsv into a DataFrame."""
    tsv_path = RESULTS_DIR / "summary.tsv"
    if not tsv_path.exists():
        print("ERROR: summary.tsv not found. Run run_judges.py first.")
        sys.exit(1)
    df = pd.read_csv(tsv_path, sep="\t")
    return df


def load_ground_truth():
    with open(GROUND_TRUTH_FILE) as f:
        return json.load(f)


def inter_judge_agreement(df, group_cols=None):
    """Compute % of criteria where ALL judges agree, grouped by optional columns."""
    if group_cols is None:
        group_cols = []

    results = []
    for condition in sorted(df["condition"].unique()):
        cond_df = df[df["condition"] == condition]

        for ctype in ["syntactic", "numeric", "semantic"]:
            type_df = cond_df[cond_df["criterion_type"] == ctype]
            if type_df.empty:
                continue

            # For each (output, criterion) pair, check if all judge×run verdicts agree
            agreements = []
            for (oid, cid), group in type_df.groupby(["output_id", "criterion"]):
                # Get unique verdicts across all judges and runs
                verdicts = group["verdict"].unique()
                agreements.append(1 if len(verdicts) == 1 else 0)

            if agreements:
                pct = np.mean(agreements) * 100
                results.append({
                    "condition": condition,
                    "criterion_type": ctype,
                    "agreement_pct": pct,
                    "n_pairs": len(agreements),
                })

    return pd.DataFrame(results)


def intra_judge_consistency(df):
    """Compute % of criteria where same judge agrees with itself across 3 runs."""
    results = []
    for model in sorted(df["model"].unique()):
        model_df = df[df["model"] == model]

        for ctype in ["syntactic", "numeric", "semantic"]:
            type_df = model_df[model_df["criterion_type"] == ctype]
            if type_df.empty:
                continue

            consistencies = []
            for (oid, cid, cond), group in type_df.groupby(["output_id", "criterion", "condition"]):
                verdicts = group["verdict"].values
                # Consistent if all runs agree
                consistencies.append(1 if len(set(verdicts)) == 1 else 0)

            if consistencies:
                pct = np.mean(consistencies) * 100
                results.append({
                    "model": model,
                    "criterion_type": ctype,
                    "consistency_pct": pct,
                    "n_groups": len(consistencies),
                })

    return pd.DataFrame(results)


def accuracy_vs_ground_truth(df):
    """Compute accuracy (match with human ground truth) by model, condition, type."""
    results = []
    for model in sorted(df["model"].unique()):
        for condition in sorted(df["condition"].unique()):
            for ctype in ["syntactic", "numeric", "semantic"]:
                subset = df[(df["model"] == model) &
                           (df["condition"] == condition) &
                           (df["criterion_type"] == ctype)]
                if subset.empty:
                    continue
                acc = subset["match"].mean() * 100
                results.append({
                    "model": model,
                    "condition": condition,
                    "criterion_type": ctype,
                    "accuracy_pct": acc,
                    "n": len(subset),
                })
    return pd.DataFrame(results)


def variance_by_criterion(df):
    """Compute a variance score (0-1) for each criterion across all judges."""
    results = []
    for (cid, ctype), group in df.groupby(["criterion", "criterion_type"]):
        # Across all models, conditions, runs: what fraction are PASS?
        pass_rate = (group["verdict"] == "PASS").mean()
        # Variance is highest at 50% (maximum disagreement)
        variance_score = 4 * pass_rate * (1 - pass_rate)  # 0 at 0% or 100%, 1 at 50%
        results.append({
            "criterion": cid,
            "criterion_type": ctype,
            "pass_rate": pass_rate,
            "variance_score": variance_score,
        })
    return pd.DataFrame(results)


def run_anova(df):
    """Run Kruskal-Wallis test: is variance different between syntactic and semantic criteria?"""
    var_df = variance_by_criterion(df)

    syntactic = var_df[var_df["criterion_type"] == "syntactic"]["variance_score"].values
    semantic = var_df[var_df["criterion_type"] == "semantic"]["variance_score"].values

    if len(syntactic) < 2 or len(semantic) < 2:
        return None, None, None, None

    stat, p = kruskal(syntactic, semantic)
    return stat, p, np.mean(syntactic), np.mean(semantic)


def pairwise_judge_agreement(df):
    """Compute pairwise agreement between each pair of judges."""
    models = sorted(df["model"].unique())
    results = {}

    for condition in sorted(df["condition"].unique()):
        cond_df = df[df["condition"] == condition]
        matrix = {}

        for i, m1 in enumerate(models):
            for j, m2 in enumerate(models):
                if i >= j:
                    continue
                # For each (output, criterion), compare majority verdicts
                agreements = []
                for (oid, cid), group in cond_df.groupby(["output_id", "criterion"]):
                    m1_verdicts = group[group["model"] == m1]["verdict"]
                    m2_verdicts = group[group["model"] == m2]["verdict"]
                    if m1_verdicts.empty or m2_verdicts.empty:
                        continue
                    # Use majority vote across runs
                    m1_majority = m1_verdicts.mode().iloc[0] if not m1_verdicts.empty else None
                    m2_majority = m2_verdicts.mode().iloc[0] if not m2_verdicts.empty else None
                    if m1_majority and m2_majority:
                        agreements.append(1 if m1_majority == m2_majority else 0)

                if agreements:
                    matrix[f"{m1} vs {m2}"] = np.mean(agreements) * 100

        results[condition] = matrix

    return results


def generate_findings(df):
    """Generate the full FINDINGS.md content."""
    lines = []
    lines.append("# E-C1 Findings: LLM Judge Variance Is Structural")
    lines.append("")
    lines.append(f"**Status:** Complete")
    lines.append(f"**Last Updated:** {pd.Timestamp.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total evaluations:** {len(df)} rows from {df['model'].nunique()} judges × {df['condition'].nunique()} conditions × {df['output_id'].nunique()} outputs × 3 runs")
    lines.append("")

    # ── Inter-Judge Agreement ──
    lines.append("## 1. Inter-Judge Agreement by Criterion Type and Condition")
    lines.append("")
    ija = inter_judge_agreement(df)
    if not ija.empty:
        pivot = ija.pivot(index="criterion_type", columns="condition", values="agreement_pct")
        lines.append(pivot.round(1).to_markdown())
    lines.append("")

    # ── Intra-Judge Consistency ──
    lines.append("## 2. Intra-Judge Self-Consistency")
    lines.append("")
    ijc = intra_judge_consistency(df)
    if not ijc.empty:
        pivot = ijc.pivot(index="model", columns="criterion_type", values="consistency_pct")
        lines.append(pivot.round(1).to_markdown())
    lines.append("")

    # ── Accuracy vs Ground Truth ──
    lines.append("## 3. Accuracy vs Human Ground Truth")
    lines.append("")
    acc = accuracy_vs_ground_truth(df)
    if not acc.empty:
        # Show by condition and type (averaged across models)
        avg_acc = acc.groupby(["condition", "criterion_type"])["accuracy_pct"].mean().reset_index()
        pivot = avg_acc.pivot(index="criterion_type", columns="condition", values="accuracy_pct")
        lines.append(pivot.round(1).to_markdown())
    lines.append("")

    # ── Pairwise Agreement ──
    lines.append("## 4. Pairwise Judge Agreement (Condition A Baseline)")
    lines.append("")
    pairwise = pairwise_judge_agreement(df)
    if "A" in pairwise:
        for pair, pct in sorted(pairwise["A"].items()):
            lines.append(f"- {pair}: {pct:.1f}%")
    lines.append("")

    # ── ANOVA ──
    lines.append("## 5. Statistical Test: Is Variance Type-Dependent?")
    lines.append("")
    stat, p, syn_mean, sem_mean = run_anova(df)
    if stat is not None:
        lines.append(f"Kruskal-Wallis H = {stat:.2f}, p = {p:.4f}")
        lines.append(f"Mean variance score — Syntactic: {syn_mean:.3f}, Semantic: {sem_mean:.3f}")
        lines.append(f"**{'Significant' if p < 0.01 else 'Not significant'}** at p < 0.01")
    lines.append("")

    # ── Hypothesis Check ──
    lines.append("## 6. Hypothesis Status")
    lines.append("")

    if not ija.empty:
        sem_a = ija[(ija["criterion_type"] == "semantic") & (ija["condition"] == "A")]
        syn_a = ija[(ija["criterion_type"] == "syntactic") & (ija["condition"] == "A")]
        sem_e = ija[(ija["criterion_type"] == "semantic") & (ija["condition"] == "E")]

        sem_a_val = sem_a["agreement_pct"].values[0] if not sem_a.empty else None
        syn_a_val = syn_a["agreement_pct"].values[0] if not syn_a.empty else None
        sem_e_val = sem_e["agreement_pct"].values[0] if not sem_e.empty else None

        # Claim 1 checks
        if sem_a_val is not None and syn_a_val is not None:
            gap = syn_a_val - sem_a_val
            lines.append(f"- [{'x' if gap > 30 else ' '}] Semantic variance > 30pp higher than syntactic: gap = {gap:.1f}pp")

        if sem_a_val is not None and sem_e_val is not None:
            improvement = sem_e_val - sem_a_val
            lines.append(f"- [{'x' if improvement < 20 else ' '}] Prompting improvement A→E < 20pp on semantic: improvement = {improvement:.1f}pp")

        if p is not None:
            lines.append(f"- [{'x' if p < 0.01 else ' '}] ANOVA p < 0.01: p = {p:.4f}")

        # Intra-judge check
        if not ijc.empty:
            sem_consistency = ijc[ijc["criterion_type"] == "semantic"]["consistency_pct"].mean()
            lines.append(f"- [{'x' if sem_consistency < 85 else ' '}] Intra-judge self-consistency < 85% for semantic: {sem_consistency:.1f}%")

    # ── Falsification ──
    lines.append("")
    lines.append("## 7. Falsification Check")
    lines.append("")
    if not ija.empty and sem_e_val is not None:
        lines.append(f"- [{'x' if sem_e_val > 90 else ' '}] Semantic agreement exceeded 90% in Condition E: {sem_e_val:.1f}%")
        if sem_e_val > 90:
            lines.append("  **⚠️ HYPOTHESIS FALSIFIED** — semantic agreement exceeds 90% with specific rubrics.")
        else:
            lines.append("  Hypothesis NOT falsified — semantic variance persists despite best prompting.")

    # ── Key Numbers for Article ──
    lines.append("")
    lines.append("## 8. Key Numbers for Article")
    lines.append("")
    if not ija.empty and sem_a_val is not None:
        sem_b = ija[(ija["criterion_type"] == "semantic") & (ija["condition"] == "B")]
        sem_b_val = sem_b["agreement_pct"].values[0] if not sem_b.empty else "?"

        lines.append(f'> "Across 10 financial model evaluations, {df["model"].nunique()} LLM judges agreed on all semantic')
        lines.append(f'> criteria only {sem_a_val:.0f}% of the time. Chain-of-thought prompting raised this to {sem_b_val}%.')
        if sem_e_val:
            lines.append(f'> The best prompting condition (explicit thresholds) reached {sem_e_val:.0f}%.')
        lines.append('> The ceiling is structural, not prompting."')

    return "\n".join(lines)


if __name__ == "__main__":
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} rows: {df['model'].nunique()} models, {df['condition'].nunique()} conditions, {df['output_id'].nunique()} outputs")

    print("\n=== Inter-Judge Agreement ===")
    ija = inter_judge_agreement(df)
    if not ija.empty:
        pivot = ija.pivot(index="criterion_type", columns="condition", values="agreement_pct")
        print(pivot.round(1).to_string())

    print("\n=== Intra-Judge Consistency ===")
    ijc = intra_judge_consistency(df)
    if not ijc.empty:
        pivot = ijc.pivot(index="model", columns="criterion_type", values="consistency_pct")
        print(pivot.round(1).to_string())

    print("\n=== Accuracy vs Ground Truth (avg across models) ===")
    acc = accuracy_vs_ground_truth(df)
    if not acc.empty:
        avg = acc.groupby(["condition", "criterion_type"])["accuracy_pct"].mean().reset_index()
        pivot = avg.pivot(index="criterion_type", columns="condition", values="accuracy_pct")
        print(pivot.round(1).to_string())

    print("\n=== ANOVA: Syntactic vs Semantic Variance ===")
    stat, p, syn_mean, sem_mean = run_anova(df)
    if stat:
        print(f"H = {stat:.2f}, p = {p:.4f}")
        print(f"Mean variance: syntactic={syn_mean:.3f}, semantic={sem_mean:.3f}")

    # Write FINDINGS.md
    print("\n=== Writing FINDINGS.md ===")
    findings = generate_findings(df)
    with open(FINDINGS_FILE, "w") as f:
        f.write(findings)
    print(f"Written to {FINDINGS_FILE}")
