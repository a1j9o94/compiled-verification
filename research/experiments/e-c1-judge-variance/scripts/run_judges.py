#!/usr/bin/env python3
"""
E-C1: LLM Judge Variance Experiment Runner

Runs 4 LLM judges × 5 prompting conditions × 3 repetitions across 10 financial model outputs.
Total: 600 API calls (~$30-50 estimated).

Usage:
    python scripts/run_judges.py                    # Run all
    python scripts/run_judges.py --condition A      # Run specific condition
    python scripts/run_judges.py --model gpt-4o     # Run specific model
    python scripts/run_judges.py --output fm-005    # Run specific output
    python scripts/run_judges.py --dry-run          # Show what would run
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from itertools import product
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
RESULTS_DIR = DATA_DIR / "results"
GROUND_TRUTH_FILE = DATA_DIR / "ground-truth" / "ground-truth.json"

# Load environment
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT.parent.parent.parent / ".env")
load_dotenv(PROJECT_ROOT.parent.parent.parent / ".env.local")
load_dotenv()

# ── Model Configuration ──────────────────────────────────────────────

MODELS = {
    "gpt-4o": {
        "provider": "openai",
        "model_id": "gpt-4o-2024-11-20",
        "env_key": "OPENAI_API_KEY",
    },
    "claude-sonnet": {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "gemini-flash": {
        "provider": "google",
        "model_id": "gemini-2.0-flash",
        "env_key": "GOOGLE_API_KEY",
        "fallback_provider": "openrouter",
        "fallback_model": "google/gemini-2.0-flash-exp:free",
        "fallback_env_key": "OPENROUTER_API_KEY",
    },
    "deepseek-v3": {
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
        "fallback_provider": "openrouter",
        "fallback_model": "deepseek/deepseek-chat",
        "fallback_env_key": "OPENROUTER_API_KEY",
    },
}

CONDITIONS = ["A", "B", "C", "D", "E"]
RUNS_PER_CONDITION = 3

# ── Rubric & Checks Text ─────────────────────────────────────────────

CHECKS_TEXT = """## Structural Integrity
- Balance sheet balances (Assets = Liabilities + Equity, every period, tolerance ±$1)
- Cash flow reconciles (ending cash on CFS = cash on BS, every period)
- P&L flows to balance sheet (net income = change in retained earnings, adjusted for dividends/SBC)
- Opening balances carry forward (each period's opening = prior period's closing)

## Formula Integrity
- No hardcoded numbers in calculation cells (revenue, COGS, expenses derive from assumptions)
- Growth rates derive from stated assumptions (not unexplained formulas)
- Unit economics are consistent (price × volume = revenue, etc.)
- No circular references (unless documented)

## Completeness
- All three statements present (P&L, balance sheet, cash flow statement)
- Assumptions page/section exists
- Time granularity is consistent throughout
- Full time horizon covered (3 years)

## Sanity Checks
- No negative revenue
- Cash doesn't go deeply negative without noted funding
- Margins are within plausible range (not >99% or <-50% without explanation)
- Headcount math works (salary × headcount × months ≈ payroll expense)
- Tax rate applied or clearly labeled pre-tax

## Formatting
- Periods are labeled
- Units are specified ($, $000s, $M, etc.)
- Inputs vs outputs are distinguished"""

RUBRIC_TEXT = """## 1. Assumption Quality (1-5)
5 — Excellent: Assumptions sourced (benchmarks, comparables), internally consistent, sensitivity ranges included.
3 — Adequate: Assumptions stated and reasonable but not sourced. No contradictions. Missing sensitivity.
1 — Failing: Assumptions unstated, contradictory, or implausible. Growth rates arbitrary.

## 2. Scenario Robustness (1-5)
5 — Excellent: Multiple scenarios with different assumption sets. Reveals what drives profitability. Break-even included.
3 — Adequate: Base case well-built. At least one alternate scenario. Break-even identifiable.
1 — Failing: Single scenario only. No sensitivity analysis.

## 3. Operational Realism (1-5)
5 — Excellent: Reflects how business operates. Hiring ramps, timing, seasonal patterns included.
3 — Adequate: Major dynamics captured. Some simplifications but nothing breaking.
1 — Failing: Purely financial, no operational logic. Revenue from nowhere. Flat percentage costs.

## 4. Cash Flow Awareness (1-5)
5 — Excellent: Cash flow is primary planning tool. Working capital modeled. Funding needs identified with timing.
3 — Adequate: Cash flow exists and reconciles. Basic funding needs identified.
1 — Failing: Cash flow missing or doesn't reconcile. No burn rate or runway.

## 5. Decision Utility (1-5)
5 — Excellent: Model is a decision tool. Change inputs, see impact. Key decisions modeled.
3 — Adequate: Projects outcomes but doesn't clearly guide decisions. Input-output traceable.
1 — Failing: Static numbers. Changing assumptions requires rebuilding. No key metrics."""

# ── Criteria List ─────────────────────────────────────────────────────

CRITERIA = [
    # Checks (binary)
    ("check_balance_sheet", "Balance sheet balances"),
    ("check_cash_flow_reconciles", "Cash flow reconciles to balance sheet"),
    ("check_pnl_flows_to_bs", "P&L flows to balance sheet (net income = RE change)"),
    ("check_opening_balances", "Opening balances carry forward"),
    ("check_no_hardcoded", "No hardcoded numbers in calculation cells"),
    ("check_growth_from_assumptions", "Growth rates derive from assumptions"),
    ("check_unit_economics_consistent", "Unit economics are consistent"),
    ("check_no_circular_refs", "No circular references"),
    ("check_three_statements", "All three statements present (P&L, BS, CFS)"),
    ("check_assumptions_page", "Assumptions page/section exists"),
    ("check_time_granularity", "Time granularity consistent"),
    ("check_full_horizon", "Full time horizon covered (3 years)"),
    ("check_no_negative_revenue", "No negative revenue"),
    ("check_cash_not_negative", "Cash doesn't go deeply negative without funding"),
    ("check_margins_plausible", "Margins within plausible range"),
    ("check_headcount_math", "Headcount math works"),
    ("check_tax_rate", "Tax rate applied or labeled pre-tax"),
    ("check_periods_labeled", "Periods are labeled"),
    ("check_units_specified", "Units are specified"),
    ("check_inputs_vs_outputs", "Inputs vs outputs distinguished"),
    # Rubric (1-5 scale, converted to PASS ≥ 3, FAIL < 3)
    ("rubric_assumption_quality", "Assumption Quality"),
    ("rubric_scenario_robustness", "Scenario Robustness"),
    ("rubric_operational_realism", "Operational Realism"),
    ("rubric_cash_flow_awareness", "Cash Flow Awareness"),
    ("rubric_decision_utility", "Decision Utility"),
]

CRITERIA_JSON = json.dumps([{"id": c[0], "name": c[1]} for c in CRITERIA], indent=2)

# ── Prompt Builders ───────────────────────────────────────────────────

def build_prompt_a(output_text: str) -> str:
    """Condition A: Baseline — minimal instruction."""
    return f"""Evaluate this financial model against the following rubric.

## Automated Checks (PASS or FAIL each)
{CHECKS_TEXT}

## Judgment Rubric (score 1-5 each, then PASS if ≥ 3, FAIL if < 3)
{RUBRIC_TEXT}

## Financial Model to Evaluate
{output_text}

## Instructions
For each criterion, output PASS or FAIL.
For rubric dimensions, also provide the numeric score (1-5).

Return your evaluation as JSON with this exact structure:
{{
  "checks": {{
    "check_balance_sheet": "PASS or FAIL",
    "check_cash_flow_reconciles": "PASS or FAIL",
    "check_pnl_flows_to_bs": "PASS or FAIL",
    "check_opening_balances": "PASS or FAIL",
    "check_no_hardcoded": "PASS or FAIL",
    "check_growth_from_assumptions": "PASS or FAIL",
    "check_unit_economics_consistent": "PASS or FAIL",
    "check_no_circular_refs": "PASS or FAIL",
    "check_three_statements": "PASS or FAIL",
    "check_assumptions_page": "PASS or FAIL",
    "check_time_granularity": "PASS or FAIL",
    "check_full_horizon": "PASS or FAIL",
    "check_no_negative_revenue": "PASS or FAIL",
    "check_cash_not_negative": "PASS or FAIL",
    "check_margins_plausible": "PASS or FAIL",
    "check_headcount_math": "PASS or FAIL",
    "check_tax_rate": "PASS or FAIL",
    "check_periods_labeled": "PASS or FAIL",
    "check_units_specified": "PASS or FAIL",
    "check_inputs_vs_outputs": "PASS or FAIL"
  }},
  "rubric_scores": {{
    "rubric_assumption_quality": <1-5>,
    "rubric_scenario_robustness": <1-5>,
    "rubric_operational_realism": <1-5>,
    "rubric_cash_flow_awareness": <1-5>,
    "rubric_decision_utility": <1-5>
  }},
  "rubric_pass_fail": {{
    "rubric_assumption_quality": "PASS or FAIL",
    "rubric_scenario_robustness": "PASS or FAIL",
    "rubric_operational_realism": "PASS or FAIL",
    "rubric_cash_flow_awareness": "PASS or FAIL",
    "rubric_decision_utility": "PASS or FAIL"
  }}
}}

Return ONLY the JSON. No explanation."""


def build_prompt_b(output_text: str) -> str:
    """Condition B: Chain-of-Thought — reason before judging."""
    return f"""Evaluate this financial model against the following rubric.

## Automated Checks (PASS or FAIL each)
{CHECKS_TEXT}

## Judgment Rubric (score 1-5 each, then PASS if ≥ 3, FAIL if < 3)
{RUBRIC_TEXT}

## Financial Model to Evaluate
{output_text}

## Instructions
For each criterion:
1. Quote or reference the relevant section of the model
2. Explain your reasoning step by step
3. Output your verdict (PASS or FAIL, and score for rubric items)

After your reasoning, return the final evaluation as JSON:
{{
  "checks": {{ ... "PASS" or "FAIL" for each ... }},
  "rubric_scores": {{ ... 1-5 for each ... }},
  "rubric_pass_fail": {{ ... "PASS" or "FAIL" for each ... }}
}}

Use the same criterion IDs as listed above. Think carefully about each criterion before deciding."""


def build_prompt_c(output_text: str) -> str:
    """Condition C: Structured Output — forced JSON with evidence fields."""
    return f"""Evaluate this financial model. Return a JSON evaluation.

## Checks
{CHECKS_TEXT}

## Rubric
{RUBRIC_TEXT}

## Model
{output_text}

Return ONLY valid JSON matching this exact schema:
{{
  "checks": {{
    "check_balance_sheet": {{"verdict": "PASS|FAIL", "evidence": "brief quote or observation"}},
    "check_cash_flow_reconciles": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_pnl_flows_to_bs": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_opening_balances": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_no_hardcoded": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_growth_from_assumptions": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_unit_economics_consistent": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_no_circular_refs": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_three_statements": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_assumptions_page": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_time_granularity": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_full_horizon": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_no_negative_revenue": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_cash_not_negative": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_margins_plausible": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_headcount_math": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_tax_rate": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_periods_labeled": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_units_specified": {{"verdict": "PASS|FAIL", "evidence": "..."}},
    "check_inputs_vs_outputs": {{"verdict": "PASS|FAIL", "evidence": "..."}}
  }},
  "rubric": {{
    "rubric_assumption_quality": {{"score": 1-5, "verdict": "PASS|FAIL", "evidence": "..."}},
    "rubric_scenario_robustness": {{"score": 1-5, "verdict": "PASS|FAIL", "evidence": "..."}},
    "rubric_operational_realism": {{"score": 1-5, "verdict": "PASS|FAIL", "evidence": "..."}},
    "rubric_cash_flow_awareness": {{"score": 1-5, "verdict": "PASS|FAIL", "evidence": "..."}},
    "rubric_decision_utility": {{"score": 1-5, "verdict": "PASS|FAIL", "evidence": "..."}}
  }}
}}"""


def build_prompt_d(output_text: str) -> str:
    """Condition D: Few-Shot — provide worked examples before evaluation."""
    pass_example = """EXAMPLE 1 (PASS):
A model with all three statements, balance sheet balances, assumptions sourced from industry benchmarks, three scenarios with different assumption sets, hiring ramps with recruiting timelines, cash flow with working capital dynamics, and decision-oriented metrics.
Result: All checks PASS. Rubric scores: Assumption Quality 4, Scenario Robustness 4, Operational Realism 5, Cash Flow Awareness 4, Decision Utility 4. All rubric dimensions PASS."""

    fail_example = """EXAMPLE 2 (FAIL):
A model missing the cash flow statement, with 100% MoM revenue growth, no assumptions page, balance sheet that doesn't balance ($3M gap), COGS as a flat 10% with no connection to operations, and no sensitivity analysis.
Result: check_balance_sheet FAIL, check_three_statements FAIL, check_assumptions_page FAIL, check_growth_from_assumptions FAIL, etc. Rubric scores all 1/5. All FAIL."""

    return f"""Evaluate this financial model against the rubric below. Here are two worked examples to calibrate your evaluation:

{pass_example}

{fail_example}

## Automated Checks
{CHECKS_TEXT}

## Judgment Rubric
{RUBRIC_TEXT}

## Financial Model to Evaluate
{output_text}

For each criterion, output PASS or FAIL. For rubric dimensions, score 1-5 (PASS if ≥ 3).

Return ONLY JSON:
{{
  "checks": {{ ... "PASS" or "FAIL" for each criterion ... }},
  "rubric_scores": {{ ... 1-5 for each dimension ... }},
  "rubric_pass_fail": {{ ... "PASS" or "FAIL" for each dimension ... }}
}}"""


def build_prompt_e(output_text: str) -> str:
    """Condition E: Rubric Specificity — explicit thresholds for every criterion."""
    return f"""Evaluate this financial model against the following detailed rubric with explicit thresholds.

## Automated Checks (PASS or FAIL each — exact thresholds given)

### Structural Integrity
- **check_balance_sheet**: Total Assets = Total Liabilities + Total Equity for EVERY period shown. Tolerance: ±$1K. If ANY period is off by more than $1K, FAIL.
- **check_cash_flow_reconciles**: Ending Cash on Cash Flow Statement = Cash on Balance Sheet for every period. If no CFS exists, automatic FAIL.
- **check_pnl_flows_to_bs**: Net Income on P&L = Change in Retained Earnings on BS (adjusted for documented dividends, SBC, or other equity transactions). Tolerance: ±$5K unless the delta is explicitly explained (e.g., SBC add-back with stated amount). Unexplained discrepancies = FAIL.
- **check_opening_balances**: Each period's opening balance = prior period's closing balance. Zero tolerance.

### Formula Integrity
- **check_no_hardcoded**: Every revenue, COGS, and expense line item must trace to an input assumption or formula. If any projection appears as a typed number without derivation, FAIL. Exception: historical actuals clearly labeled.
- **check_growth_from_assumptions**: If revenue grows X%, there must be a stated assumption that says X% and a source or rationale. "= prior × 1.15" with no reference to why 15% = FAIL.
- **check_unit_economics_consistent**: Price × Volume = Revenue (or equivalent) must hold. COGS per unit × volume = total COGS. If unit economics exist but don't tie out, FAIL.
- **check_no_circular_refs**: No circular references unless explicitly documented with iteration methodology. If the model references itself (even implicitly), FAIL.

### Completeness
- **check_three_statements**: Income Statement, Balance Sheet, AND Cash Flow Statement must all be present as separate, labeled sections. "Cash projections embedded in balance sheet" or "CFS to be completed later" = FAIL.
- **check_assumptions_page**: A clearly labeled assumptions section/table exists listing key input variables. Assumptions scattered only within other tables = FAIL.
- **check_time_granularity**: Consistent throughout (all annual, all monthly, etc.). Mixed granularity without clear justification = FAIL.
- **check_full_horizon**: If 3 years specified, all 3 years must be present for all three statements.

### Sanity Checks
- **check_no_negative_revenue**: Revenue ≥ $0 in all periods. Any negative revenue = FAIL unless explicitly modeling refunds.
- **check_cash_not_negative**: If cash goes below -$50K for more than one period without documented funding source (debt raise, equity raise), FAIL.
- **check_margins_plausible**: Gross margin must be between -50% and 95% for non-software businesses, or between -50% and 99% for software/SaaS. Operating margin > 50% requires explanation. Anything outside these ranges = FAIL.
- **check_headcount_math**: If headcount and payroll are both modeled: total salary expense should be within ±20% of (avg salary × headcount × period). If they diverge by more than 20%, FAIL.
- **check_tax_rate**: Either (a) tax provision line exists, or (b) model clearly states "pre-tax" or "NOL carryforward — 0% effective rate." No mention of taxes at all = FAIL.

### Formatting
- **check_periods_labeled**: Every column has a date or period label (Y1, Month 1, Q1 2026, etc.). Unlabeled columns = FAIL.
- **check_units_specified**: Currency denomination stated at least once ($, $000s, $M). If amounts appear with no unit context = FAIL.
- **check_inputs_vs_outputs**: Assumptions/inputs are in a separate section OR clearly marked. If inputs and calculations are interleaved with no visual/structural distinction = FAIL.

## Judgment Rubric (score 1-5 each, PASS if ≥ 3, FAIL if < 3)

### rubric_assumption_quality
- **5**: ALL key assumptions (revenue growth, margins, retention, churn, headcount costs) have (a) stated values, (b) external sources or rationale, and (c) sensitivity ranges.
- **4**: Key assumptions stated with sources for most. Missing sensitivity ranges OR missing source for 1-2 assumptions.
- **3**: Assumptions stated and reasonable but ZERO external sources. No contradictions.
- **2**: Assumptions stated but some are unreasonable (>50% MoM growth, 95%+ margins without justification), OR internal contradictions present.
- **1**: Key assumptions missing or implausible. Growth rates arbitrary.

### rubric_scenario_robustness
- **5**: ≥3 scenarios varying different assumption sets. Tornado/sensitivity identifying top drivers. Break-even analysis.
- **4**: 3 scenarios present but may not vary the right assumptions. Sensitivity exists but not comprehensive.
- **3**: Base case + at least 1 alternate scenario. OR base case + sensitivity on ≥2 variables.
- **2**: Only 1 sensitivity dimension (e.g., revenue ±10% only). No alternate scenarios.
- **1**: Single scenario. No sensitivity. No way to stress-test.

### rubric_operational_realism
- **5**: Hiring ramps with recruiting timelines, seasonal patterns, capacity constraints, marketing-to-revenue lag modeled.
- **4**: Major operational dynamics captured. Hiring plan exists with ramp assumptions. Minor simplifications.
- **3**: Headcount plan exists. Revenue doesn't start at full run rate. Major dynamics acknowledged even if simplified.
- **2**: Some operational awareness but key dynamics missing (instant hiring, revenue from day 1, costs as flat percentages).
- **1**: Purely financial. Revenue and costs are disconnected from operations.

### rubric_cash_flow_awareness
- **5**: Cash flow statement with working capital (AR, AP, deferred revenue). Burn rate, runway, funding timing identified.
- **4**: CFS exists and reconciles. Basic funding needs identified. Working capital simplified but present.
- **3**: CFS exists OR cash dynamics discussed. Burn rate calculable from model.
- **2**: Cash mentioned but not formally modeled. "Approximate" cash projections.
- **1**: No cash flow consideration. No burn rate. No runway.

### rubric_decision_utility
- **5**: Model answers "what should we do?" — hiring triggers, fundraise timing, pricing experiments modeled.
- **4**: Key metrics (LTV/CAC, burn multiple, magic number) calculated. Input changes ripple through.
- **3**: Metrics exist. Model can be used for planning with additional work.
- **2**: Projects numbers but doesn't guide decisions. Limited metrics.
- **1**: Static. No "what-if" capability. Presentation-only.

## Financial Model to Evaluate
{output_text}

Return ONLY JSON:
{{
  "checks": {{ ... "PASS" or "FAIL" for each criterion ... }},
  "rubric_scores": {{ ... 1-5 for each dimension ... }},
  "rubric_pass_fail": {{ ... "PASS" or "FAIL" for each dimension ... }}
}}"""


PROMPT_BUILDERS = {
    "A": build_prompt_a,
    "B": build_prompt_b,
    "C": build_prompt_c,
    "D": build_prompt_d,
    "E": build_prompt_e,
}

# ── API Callers ───────────────────────────────────────────────────────

def call_openai(model_id: str, prompt: str, temperature: float = 0.3) -> str:
    """Call OpenAI API."""
    import openai
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def call_anthropic(model_id: str, prompt: str, temperature: float = 0.3) -> str:
    """Call Anthropic API."""
    import anthropic
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model_id,
        max_tokens=4096,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def call_google(model_id: str, prompt: str, temperature: float = 0.3) -> str:
    """Call Google Generative AI."""
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(model_id)
    response = model.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": 4096},
    )
    return response.text


def call_openrouter(model_id: str, prompt: str, temperature: float = 0.3) -> str:
    """Call OpenRouter (for Gemini/DeepSeek fallback)."""
    import openai
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def call_deepseek(model_id: str, prompt: str, temperature: float = 0.3) -> str:
    """Call DeepSeek API (OpenAI-compatible)."""
    import openai
    client = openai.OpenAI(
        base_url="https://api.deepseek.com",
        api_key=os.environ["DEEPSEEK_API_KEY"],
    )
    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def get_caller(model_key: str):
    """Get the appropriate API caller and model ID for a model key."""
    config = MODELS[model_key]

    # Try primary provider
    if os.environ.get(config["env_key"]):
        if config["provider"] == "openai":
            return call_openai, config["model_id"]
        elif config["provider"] == "anthropic":
            return call_anthropic, config["model_id"]
        elif config["provider"] == "google":
            return call_google, config["model_id"]
        elif config["provider"] == "deepseek":
            return call_deepseek, config["model_id"]

    # Try fallback (OpenRouter)
    if "fallback_provider" in config and os.environ.get(config.get("fallback_env_key", "")):
        return call_openrouter, config["fallback_model"]

    return None, None


# ── Result Parsing ────────────────────────────────────────────────────

def extract_json(text: str) -> dict:
    """Extract JSON from model response, handling markdown code blocks."""
    # Try direct parse
    text = text.strip()

    # Remove markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Find opening and closing ```
        start = 1  # skip first ```json line
        end = len(lines) - 1
        for i in range(len(lines) - 1, 0, -1):
            if lines[i].strip().startswith("```"):
                end = i
                break
        text = "\n".join(lines[start:end])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON in the text
        brace_start = text.find("{")
        brace_end = text.rfind("}") + 1
        if brace_start >= 0 and brace_end > brace_start:
            try:
                return json.loads(text[brace_start:brace_end])
            except json.JSONDecodeError:
                pass

    return None


def normalize_verdicts(parsed: dict) -> dict:
    """Normalize parsed JSON into standard {criterion_id: "PASS"|"FAIL"} format."""
    result = {}

    if not parsed:
        return result

    # Handle checks
    checks = parsed.get("checks", {})
    for cid, val in checks.items():
        if isinstance(val, str):
            result[cid] = "PASS" if "PASS" in val.upper() else "FAIL"
        elif isinstance(val, dict):
            verdict = val.get("verdict", val.get("result", ""))
            result[cid] = "PASS" if "PASS" in str(verdict).upper() else "FAIL"

    # Handle rubric scores — convert to PASS/FAIL
    rubric_pf = parsed.get("rubric_pass_fail", {})
    rubric_scores = parsed.get("rubric_scores", parsed.get("rubric", {}))

    for cid in ["rubric_assumption_quality", "rubric_scenario_robustness",
                 "rubric_operational_realism", "rubric_cash_flow_awareness",
                 "rubric_decision_utility"]:
        # Try rubric_pass_fail first
        if cid in rubric_pf:
            val = rubric_pf[cid]
            result[cid] = "PASS" if "PASS" in str(val).upper() else "FAIL"
        # Fall back to score
        elif cid in rubric_scores:
            val = rubric_scores[cid]
            if isinstance(val, dict):
                score = val.get("score", 0)
                verdict = val.get("verdict", "")
                if verdict:
                    result[cid] = "PASS" if "PASS" in str(verdict).upper() else "FAIL"
                else:
                    result[cid] = "PASS" if int(score) >= 3 else "FAIL"
            elif isinstance(val, (int, float)):
                result[cid] = "PASS" if val >= 3 else "FAIL"
            elif isinstance(val, str):
                result[cid] = "PASS" if "PASS" in val.upper() else "FAIL"

    return result


# ── Main Runner ───────────────────────────────────────────────────────

def load_outputs() -> dict:
    """Load all financial model outputs."""
    outputs = {}
    for f in sorted(OUTPUTS_DIR.glob("fm-*.md")):
        outputs[f.stem] = f.read_text()
    return outputs


def load_ground_truth() -> dict:
    """Load ground truth verdicts."""
    with open(GROUND_TRUTH_FILE) as f:
        return json.load(f)


def result_exists(model_key: str, condition: str, run: int, output_id: str) -> bool:
    """Check if a result file already exists."""
    path = RESULTS_DIR / f"{model_key}-{condition}-run{run}-{output_id}.json"
    return path.exists()


def save_result(model_key: str, condition: str, run: int, output_id: str,
                raw_response: str, parsed: dict, verdicts: dict, elapsed: float):
    """Save result to JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    result = {
        "model": model_key,
        "condition": condition,
        "run": run,
        "output_id": output_id,
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "raw_response": raw_response,
        "parsed": parsed,
        "verdicts": verdicts,
    }

    path = RESULTS_DIR / f"{model_key}-{condition}-run{run}-{output_id}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2)


def update_summary_tsv(ground_truth: dict):
    """Regenerate summary.tsv from all result files."""
    gt_verdicts = ground_truth["verdicts"]
    gt_criteria = {c["id"]: c["type"] for c in ground_truth["criteria"]}

    rows = []
    for result_file in sorted(RESULTS_DIR.glob("*.json")):
        with open(result_file) as f:
            result = json.load(f)

        output_id = result["output_id"]
        model = result["model"]
        condition = result["condition"]
        run = result["run"]
        verdicts = result.get("verdicts", {})

        gt_output = gt_verdicts.get(output_id, {})
        gt_checks = gt_output.get("checks", {})
        gt_rubric_pf = gt_output.get("rubric_pass_fail", {})
        gt_all = {**gt_checks, **gt_rubric_pf}

        for cid, verdict in verdicts.items():
            ctype = gt_criteria.get(cid, "unknown")
            gt_verdict = gt_all.get(cid, "")
            match = 1 if verdict == gt_verdict else 0
            rows.append(f"{model}\t{condition}\t{run}\t{output_id}\t{cid}\t{ctype}\t{verdict}\t{gt_verdict}\t{match}")

    header = "model\tcondition\trun\toutput_id\tcriterion\tcriterion_type\tverdict\tground_truth\tmatch"
    tsv_path = RESULTS_DIR / "summary.tsv"
    with open(tsv_path, "w") as f:
        f.write(header + "\n")
        f.write("\n".join(rows) + "\n")

    print(f"  Summary TSV updated: {len(rows)} rows → {tsv_path}")


def main():
    parser = argparse.ArgumentParser(description="E-C1 Judge Variance Runner")
    parser.add_argument("--condition", choices=CONDITIONS, help="Run specific condition only")
    parser.add_argument("--model", choices=list(MODELS.keys()), help="Run specific model only")
    parser.add_argument("--output", help="Run specific output only (e.g., fm-005)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would run without calling APIs")
    parser.add_argument("--temperature", type=float, default=0.3, help="Temperature for API calls")
    args = parser.parse_args()

    # Load data
    outputs = load_outputs()
    ground_truth = load_ground_truth()
    print(f"Loaded {len(outputs)} outputs, {len(ground_truth['criteria'])} criteria")

    # Check available models
    available_models = {}
    for model_key in MODELS:
        caller, model_id = get_caller(model_key)
        if caller:
            available_models[model_key] = (caller, model_id)
            print(f"  ✓ {model_key} → {model_id}")
        else:
            print(f"  ✗ {model_key} — no API key available, skipping")

    if not available_models:
        print("ERROR: No models available. Set API keys in environment.")
        sys.exit(1)

    # Filter based on args
    models_to_run = [args.model] if args.model else list(available_models.keys())
    conditions_to_run = [args.condition] if args.condition else CONDITIONS
    outputs_to_run = [args.output] if args.output else list(outputs.keys())

    # Count work
    total = 0
    skipped = 0
    for output_id, model_key, condition in product(outputs_to_run, models_to_run, conditions_to_run):
        if model_key not in available_models:
            continue
        for run in range(1, RUNS_PER_CONDITION + 1):
            if result_exists(model_key, condition, run, output_id):
                skipped += 1
            else:
                total += 1

    print(f"\nPlan: {total} API calls to make, {skipped} already complete")

    if args.dry_run:
        print("(dry run — exiting)")
        return

    # Run experiments
    completed = 0
    errors = 0

    for condition in conditions_to_run:
        for model_key in models_to_run:
            if model_key not in available_models:
                continue
            caller, model_id = available_models[model_key]

            for output_id in outputs_to_run:
                for run in range(1, RUNS_PER_CONDITION + 1):
                    if result_exists(model_key, condition, run, output_id):
                        continue

                    label = f"[{model_key}|{condition}|run{run}|{output_id}]"
                    print(f"  {label} calling...", end=" ", flush=True)

                    prompt = PROMPT_BUILDERS[condition](outputs[output_id])

                    try:
                        start_time = time.time()
                        raw = caller(model_id, prompt, temperature=args.temperature)
                        elapsed = time.time() - start_time

                        parsed = extract_json(raw)
                        verdicts = normalize_verdicts(parsed)

                        save_result(model_key, condition, run, output_id,
                                   raw, parsed, verdicts, elapsed)

                        n_verdicts = len(verdicts)
                        completed += 1
                        print(f"OK ({elapsed:.1f}s, {n_verdicts} verdicts) [{completed}/{total}]")

                    except Exception as e:
                        # Retry once per program.md
                        print(f"RETRY ({e})", end=" ", flush=True)
                        try:
                            time.sleep(2)
                            start_time = time.time()
                            raw = caller(model_id, prompt, temperature=args.temperature)
                            elapsed = time.time() - start_time

                            parsed = extract_json(raw)
                            verdicts = normalize_verdicts(parsed)

                            save_result(model_key, condition, run, output_id,
                                       raw, parsed, verdicts, elapsed)

                            completed += 1
                            print(f"OK on retry ({elapsed:.1f}s)")

                        except Exception as e2:
                            errors += 1
                            # Log crash and skip
                            save_result(model_key, condition, run, output_id,
                                       f"CRASH: {e2}", None, {}, 0)
                            print(f"CRASH: {e2}")

                    # Rate limiting — small delay between calls
                    time.sleep(0.5)

    print(f"\nDone: {completed} completed, {errors} errors, {skipped} skipped (already existed)")

    # Update summary
    print("Updating summary.tsv...")
    update_summary_tsv(ground_truth)


if __name__ == "__main__":
    main()
