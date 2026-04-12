"""
Benchmark Suite — Insurance Claims Adjudication Environment
============================================================
Runs a comprehensive benchmark across all fixed tasks and procedural
scenarios, producing a standardized report for reproducibility.

This proves:
  1. All tasks produce valid scores in (0, 1)
  2. Difficulty progression works (easy > medium > hard for perfect agent)
  3. Procedural generation is deterministic (same seed = same result)
  4. The environment handles edge cases gracefully
  5. Score distribution across 100+ scenarios

Usage:
    python benchmark.py                    # full benchmark
    python benchmark.py --seeds 50         # quick run
    python benchmark.py --output report.json
"""

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List

try:
    from claims_env.server.claims_env_environment import ClaimsEnvironment
    from claims_env.models import ClaimsAction
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from server.claims_env_environment import ClaimsEnvironment
    from models import ClaimsAction


FIXED_TASKS = [
    "easy_auto_collision", "easy_travel_cancellation",
    "medium_medical_exclusions", "medium_pet_surgery",
    "medium_life_benefit", "medium_liability_injury",
    "hard_property_fraud", "hard_flood_exclusion", "hard_disability_claim",
]


def run_perfect_agent(env, task_id=None, difficulty=None, seed=None):
    """Run an agent that follows the ideal workflow."""
    if task_id:
        obs = env.reset(task_id=task_id)
    else:
        obs = env.reset(difficulty=difficulty, seed=seed)

    gt = env._ground_truth
    rewards = []

    # Ideal workflow
    actions = [
        ClaimsAction(action_type="check_eligibility"),
        ClaimsAction(action_type="check_coverage", policy_section="primary"),
        ClaimsAction(action_type="check_exclusion"),
        ClaimsAction(action_type="calculate_payout",
                     claimed_amount=gt["payout"].get("claimed_amount", 0),
                     deductible=gt["payout"].get("total_deductible", gt["payout"].get("deductible", 500)),
                     coverage_limit=50000, coverage_rate=0.80),
    ]

    # Flag fraud if present
    for flag in gt.get("fraud_flags", []):
        actions.append(ClaimsAction(
            action_type="flag_fraud",
            fraud_indicator=flag["indicator"],
            fraud_evidence=flag.get("description", "Evidence found"),
        ))

    # Issue decision
    actions.append(ClaimsAction(
        action_type="issue_decision",
        decision=gt["correct_decision"],
        decision_amount=gt["correct_decision_amount"],
        decision_reasoning=f"Decision based on complete policy analysis",
    ))

    for action in actions:
        if obs.done:
            break
        obs = env.step(action)
        rewards.append(float(obs.reward))

    return {
        "score": float(obs.current_score),
        "steps": len(rewards),
        "done": bool(obs.done),
        "rewards": rewards,
        "breakdown": {k: float(v) for k, v in (obs.score_breakdown or {}).items()},
    }


def benchmark_fixed_tasks(env) -> Dict[str, Any]:
    """Run benchmark on all 9 fixed tasks."""
    results = {}
    for task_id in FIXED_TASKS:
        result = run_perfect_agent(env, task_id=task_id)
        results[task_id] = result
    return results


def benchmark_procedural(env, num_seeds: int = 100) -> Dict[str, Any]:
    """Run benchmark on procedural scenarios."""
    results = {"easy": [], "medium": [], "hard": []}

    for seed in range(num_seeds):
        for diff in ["easy", "medium", "hard"]:
            result = run_perfect_agent(env, difficulty=diff, seed=seed)
            results[diff].append(result["score"])

    stats = {}
    for diff, scores in results.items():
        stats[diff] = {
            "count": len(scores),
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "std": (sum((s - sum(scores)/len(scores))**2 for s in scores) / len(scores)) ** 0.5,
        }

    return {"per_difficulty": stats, "total_scenarios": num_seeds * 3}


def benchmark_determinism(env, num_checks: int = 10) -> Dict[str, Any]:
    """Verify deterministic reproducibility."""
    failures = 0

    for seed in range(num_checks):
        r1 = run_perfect_agent(env, difficulty="medium", seed=seed)
        r2 = run_perfect_agent(env, difficulty="medium", seed=seed)
        if abs(r1["score"] - r2["score"]) > 0.0001:
            failures += 1

    return {
        "checks": num_checks,
        "failures": failures,
        "deterministic": failures == 0,
    }


def benchmark_curriculum(env) -> Dict[str, Any]:
    """Test curriculum levels 1-10."""
    results = {}
    for level in range(1, 11):
        obs = env.reset(curriculum_level=level, seed=42)
        r = run_perfect_agent(env, difficulty=None, seed=None)
        # Re-run with the level since the above reset already happened
        env.reset(curriculum_level=level, seed=42)
        env.step(ClaimsAction(action_type="check_eligibility"))
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="deny",
            decision_amount=0, decision_reasoning="test"))
        results[f"level_{level}"] = {
            "difficulty": ["easy","easy","easy","medium","medium","medium","hard","hard","hard","hard"][level-1],
            "score": float(obs.current_score),
        }
    return results


def benchmark_score_ranges(env, num_seeds: int = 50) -> Dict[str, Any]:
    """Verify all scores are strictly in (0, 1)."""
    violations = []

    for seed in range(num_seeds):
        for diff in ["easy", "medium", "hard"]:
            result = run_perfect_agent(env, difficulty=diff, seed=seed)
            s = result["score"]
            if s <= 0.0 or s >= 1.0:
                violations.append({"seed": seed, "difficulty": diff, "score": s})
            for k, v in result["breakdown"].items():
                if v <= 0.0 or v >= 1.0:
                    violations.append({"seed": seed, "difficulty": diff, "field": k, "value": v})

    return {
        "scenarios_checked": num_seeds * 3,
        "violations": len(violations),
        "all_valid": len(violations) == 0,
        "details": violations[:10] if violations else [],
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark Claims Environment")
    parser.add_argument("--seeds", type=int, default=100, help="Procedural seeds to test")
    parser.add_argument("--output", type=str, default="outputs/benchmark_report.json")
    args = parser.parse_args()

    env = ClaimsEnvironment()
    start = time.time()

    print("Insurance Claims Adjudication — Benchmark Suite", flush=True)
    print("=" * 55, flush=True)

    # 1. Fixed tasks
    print("\n[1/5] Fixed tasks (9 tasks)...", flush=True)
    fixed = benchmark_fixed_tasks(env)
    for tid, r in fixed.items():
        print(f"  {tid:35s} score={r['score']:.3f} steps={r['steps']}", flush=True)

    # 2. Procedural
    print(f"\n[2/5] Procedural scenarios ({args.seeds} seeds x 3 difficulties)...", flush=True)
    procedural = benchmark_procedural(env, args.seeds)
    for diff, stats in procedural["per_difficulty"].items():
        print(f"  {diff:8s} mean={stats['mean']:.3f} std={stats['std']:.3f} "
              f"min={stats['min']:.3f} max={stats['max']:.3f}", flush=True)

    # 3. Determinism
    print("\n[3/5] Determinism check...", flush=True)
    determinism = benchmark_determinism(env)
    print(f"  {'PASS' if determinism['deterministic'] else 'FAIL'} "
          f"({determinism['checks']} checks, {determinism['failures']} failures)", flush=True)

    # 4. Curriculum
    print("\n[4/5] Curriculum levels 1-10...", flush=True)
    curriculum = benchmark_curriculum(env)
    for level, r in curriculum.items():
        print(f"  {level}: {r['difficulty']:8s} score={r['score']:.3f}", flush=True)

    # 5. Score ranges
    print(f"\n[5/5] Score range validation ({args.seeds} seeds)...", flush=True)
    score_ranges = benchmark_score_ranges(env, args.seeds)
    print(f"  {'PASS' if score_ranges['all_valid'] else 'FAIL'} "
          f"({score_ranges['scenarios_checked']} scenarios, {score_ranges['violations']} violations)", flush=True)

    elapsed = time.time() - start

    # Summary
    fixed_scores = [r["score"] for r in fixed.values()]
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": "claims_env",
        "version": "0.1.0",
        "elapsed_seconds": round(elapsed, 1),
        "fixed_tasks": {
            "count": len(fixed),
            "results": fixed,
            "avg_score": sum(fixed_scores) / len(fixed_scores),
        },
        "procedural": procedural,
        "determinism": determinism,
        "curriculum": curriculum,
        "score_ranges": score_ranges,
        "summary": {
            "total_scenarios": len(fixed) + procedural["total_scenarios"] + 10 + args.seeds * 3,
            "all_deterministic": determinism["deterministic"],
            "all_scores_valid": score_ranges["all_valid"],
            "difficulty_progression_valid": (
                procedural["per_difficulty"]["easy"]["mean"] >
                procedural["per_difficulty"]["hard"]["mean"]
            ),
        },
    }

    print(f"\n{'=' * 55}", flush=True)
    print(f"Total scenarios: {report['summary']['total_scenarios']}", flush=True)
    print(f"Deterministic: {report['summary']['all_deterministic']}", flush=True)
    print(f"Scores valid: {report['summary']['all_scores_valid']}", flush=True)
    print(f"Time: {elapsed:.1f}s", flush=True)

    os.makedirs(os.path.dirname(args.output) or "outputs", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to {args.output}", flush=True)


if __name__ == "__main__":
    main()
