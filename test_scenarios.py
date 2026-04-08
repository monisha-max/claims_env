"""
Scenario Test Agent — validates the environment across many procedurally
generated scenarios + all fixed tasks.

Runs a deterministic "perfect agent" that uses ground truth to take the
correct actions, verifying that the grading logic is consistent.

Also runs a "random agent" to verify robustness under unexpected inputs.

Usage:
    python test_scenarios.py                    # run all tests
    python test_scenarios.py --seeds 500        # test 500 procedural seeds
    python test_scenarios.py --verbose          # show details per scenario
"""

import argparse
import json
import random
import sys
import time
from typing import Any, Dict, List

try:
    from claims_env.server.claims_env_environment import ClaimsEnvironment
    from claims_env.models import ClaimsAction
except ImportError:
    from server.claims_env_environment import ClaimsEnvironment
    from models import ClaimsAction

# ─── Perfect Agent ───────────────────────────────────────────────────


def run_perfect_agent(env: ClaimsEnvironment, task_id: str = None,
                      difficulty: str = None, seed: int = None,
                      insurance_type: str = None) -> Dict[str, Any]:
    """Run a perfect agent that uses ground truth to take optimal actions."""
    if task_id:
        obs = env.reset(task_id=task_id)
    else:
        obs = env.reset(difficulty=difficulty, insurance_type=insurance_type, seed=seed)

    gt = env._ground_truth
    task = env._task
    steps = 0
    errors = []

    # Step 1: Check eligibility
    obs = env.step(ClaimsAction(
        action_type="check_eligibility",
        policy_id=task.get("_policy_data", {}).get("id", "test"),
        incident_date=task.get("_claim_data", {}).get("incident_date", "2024-06-01"),
    ))
    steps += 1

    # Step 2: Check coverage
    obs = env.step(ClaimsAction(
        action_type="check_coverage",
        policy_section=gt["coverage"].get("section", "auto"),
        claim_item="all",
    ))
    steps += 1

    # Step 3: Check exclusions
    obs = env.step(ClaimsAction(
        action_type="check_exclusion",
        policy_section="exclusions",
        claim_item="all",
    ))
    steps += 1

    # Step 4: Calculate payout
    payout_info = gt["payout"]
    claimed = payout_info.get("claimed_amount", payout_info.get("correct_payout", 0))
    deductible = payout_info.get("total_deductible", payout_info.get("deductible", 0))
    obs = env.step(ClaimsAction(
        action_type="calculate_payout",
        claimed_amount=claimed,
        deductible=deductible,
        coverage_limit=100000,
        coverage_rate=0.80,
    ))
    steps += 1

    # Step 5: Flag fraud (if any)
    for flag in gt.get("fraud_flags", []):
        obs = env.step(ClaimsAction(
            action_type="flag_fraud",
            fraud_indicator=flag["indicator"],
            fraud_evidence=flag.get("description", "Evidence found"),
        ))
        steps += 1

    # Step 6: Issue decision
    obs = env.step(ClaimsAction(
        action_type="issue_decision",
        decision=gt["correct_decision"],
        decision_amount=gt["correct_decision_amount"],
        decision_reasoning=f"Decision based on policy analysis: {gt['correct_decision']}",
    ))
    steps += 1

    # Validate
    if not obs.done:
        errors.append("Episode did not end after decision")
    if obs.current_score <= 0:
        errors.append(f"Score is {obs.current_score}, expected > 0")

    return {
        "task_id": obs.task_id,
        "score": obs.current_score,
        "steps": steps,
        "done": obs.done,
        "errors": errors,
        "score_breakdown": obs.score_breakdown,
    }


# ─── Random Agent ────────────────────────────────────────────────────


def run_random_agent(env: ClaimsEnvironment, difficulty: str = "medium",
                     seed: int = None, max_steps: int = 10) -> Dict[str, Any]:
    """Run a random agent to test environment robustness."""
    rng = random.Random(seed)
    obs = env.reset(difficulty=difficulty, seed=seed)

    errors = []
    steps = 0

    action_types = [
        "check_eligibility", "check_coverage", "check_exclusion",
        "calculate_payout", "flag_fraud", "request_info",
    ]

    for _ in range(max_steps - 1):
        action_type = rng.choice(action_types)

        try:
            if action_type == "check_eligibility":
                action = ClaimsAction(action_type=action_type, policy_id="test", incident_date="2024-06-01")
            elif action_type == "check_coverage":
                action = ClaimsAction(action_type=action_type, policy_section="auto", claim_item="bumper")
            elif action_type == "check_exclusion":
                action = ClaimsAction(action_type=action_type, policy_section="exclusions", claim_item="test")
            elif action_type == "calculate_payout":
                action = ClaimsAction(
                    action_type=action_type,
                    claimed_amount=rng.uniform(1000, 50000),
                    deductible=rng.uniform(0, 5000),
                    coverage_limit=rng.uniform(10000, 100000),
                    coverage_rate=rng.uniform(0.5, 1.0),
                )
            elif action_type == "flag_fraud":
                action = ClaimsAction(
                    action_type=action_type,
                    fraud_indicator=rng.choice(["timing", "inflated", "suspicious", "random_flag"]),
                    fraud_evidence="Test evidence",
                )
            else:
                action = ClaimsAction(action_type=action_type, info_question="What is the coverage?")

            obs = env.step(action)
            steps += 1

            if obs.done:
                break

        except Exception as e:
            errors.append(f"Step {steps}: {action_type} raised {type(e).__name__}: {e}")
            break

    # Force decision if not done
    if not obs.done:
        try:
            obs = env.step(ClaimsAction(
                action_type="issue_decision",
                decision=rng.choice(["approve", "deny", "partial_approve"]),
                decision_amount=rng.uniform(0, 50000),
                decision_reasoning="Random decision",
            ))
            steps += 1
        except Exception as e:
            errors.append(f"Decision raised {type(e).__name__}: {e}")

    return {
        "task_id": obs.task_id if obs else "unknown",
        "score": obs.current_score if obs else 0,
        "steps": steps,
        "done": getattr(obs, "done", False),
        "errors": errors,
    }


# ─── Main Test Runner ────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Test claims environment scenarios")
    parser.add_argument("--seeds", type=int, default=100, help="Number of procedural seeds to test")
    parser.add_argument("--verbose", action="store_true", help="Show per-scenario details")
    args = parser.parse_args()

    env = ClaimsEnvironment()
    start_time = time.time()
    all_results = []
    failures = []

    # ─── Test 1: All fixed tasks with perfect agent ──────────────────
    print("=" * 60)
    print("TEST 1: Perfect agent on all fixed tasks")
    print("=" * 60)

    fixed_tasks = [
        "easy_auto_collision", "easy_travel_cancellation",
        "medium_medical_exclusions", "medium_pet_surgery",
        "medium_life_benefit", "medium_liability_injury",
        "hard_property_fraud", "hard_flood_exclusion", "hard_disability_claim",
    ]

    for task_id in fixed_tasks:
        result = run_perfect_agent(env, task_id=task_id)
        status = "PASS" if not result["errors"] and result["score"] > 0 else "FAIL"
        if result["errors"]:
            failures.append(f"Fixed/{task_id}: {result['errors']}")
        print(f"  [{status}] {task_id:30s} score={result['score']:.3f} steps={result['steps']}")
        if args.verbose and result["score_breakdown"]:
            for cat, s in sorted(result["score_breakdown"].items()):
                print(f"         {cat}: {s:.3f}")
        all_results.append(result)

    # ─── Test 2: Perfect agent on procedural scenarios ───────────────
    print(f"\n{'=' * 60}")
    print(f"TEST 2: Perfect agent on {args.seeds} procedural scenarios")
    print("=" * 60)

    proc_scores = {"easy": [], "medium": [], "hard": []}
    proc_types = {"auto": 0, "medical": 0, "home": 0, "travel": 0}
    proc_errors = 0

    for seed in range(args.seeds):
        for diff in ["easy", "medium", "hard"]:
            result = run_perfect_agent(env, difficulty=diff, seed=seed)
            proc_scores[diff].append(result["score"])
            if result["errors"]:
                proc_errors += 1
                failures.append(f"Procedural/seed={seed}/{diff}: {result['errors']}")

            # Track insurance types
            itype = result["task_id"].split("_")[1] if result["task_id"] else "unknown"
            if itype in proc_types:
                proc_types[itype] += 1

            if args.verbose:
                print(f"  seed={seed:3d} diff={diff:6s} score={result['score']:.3f} "
                      f"task={result['task_id']}")

    for diff in ["easy", "medium", "hard"]:
        scores = proc_scores[diff]
        avg = sum(scores) / len(scores) if scores else 0
        mn = min(scores) if scores else 0
        mx = max(scores) if scores else 0
        print(f"  {diff:6s}: avg={avg:.3f} min={mn:.3f} max={mx:.3f} count={len(scores)}")

    print(f"  Types: {proc_types}")
    print(f"  Errors: {proc_errors}/{args.seeds * 3}")

    # ─── Test 3: Random agent robustness ─────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"TEST 3: Random agent robustness ({args.seeds} scenarios)")
    print("=" * 60)

    random_errors = 0
    random_crashes = 0

    for seed in range(args.seeds):
        diff = random.choice(["easy", "medium", "hard"])
        try:
            result = run_random_agent(env, difficulty=diff, seed=seed)
            if result["errors"]:
                random_errors += 1
                if args.verbose:
                    print(f"  seed={seed}: {result['errors']}")
        except Exception as e:
            random_crashes += 1
            failures.append(f"Random/seed={seed}: CRASH {type(e).__name__}: {e}")

    print(f"  Completed: {args.seeds - random_crashes}/{args.seeds}")
    print(f"  Non-fatal errors: {random_errors}")
    print(f"  Crashes: {random_crashes}")

    # ─── Test 4: Reproducibility ─────────────────────────────────────
    print(f"\n{'=' * 60}")
    print("TEST 4: Reproducibility (same seed = same scenario)")
    print("=" * 60)

    repro_pass = 0
    repro_fail = 0
    for seed in [42, 123, 456, 789, 1000]:
        r1 = run_perfect_agent(env, difficulty="medium", seed=seed)
        r2 = run_perfect_agent(env, difficulty="medium", seed=seed)
        if abs(r1["score"] - r2["score"]) < 0.001:
            repro_pass += 1
        else:
            repro_fail += 1
            failures.append(f"Reproducibility/seed={seed}: {r1['score']} != {r2['score']}")

    print(f"  Passed: {repro_pass}/5, Failed: {repro_fail}/5")

    # ─── Summary ─────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    total_tests = len(fixed_tasks) + args.seeds * 3 + args.seeds + 5
    total_failures = len(failures)

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total tests: {total_tests}")
    print(f"  Failures: {total_failures}")
    print(f"  Time: {elapsed:.1f}s")

    if failures:
        print(f"\n  FAILURES:")
        for f in failures[:20]:
            print(f"    - {f}")
        if len(failures) > 20:
            print(f"    ... and {len(failures) - 20} more")

    if total_failures == 0:
        print(f"\n  ALL TESTS PASSED")
    else:
        print(f"\n  {total_failures} TESTS FAILED")

    # Save results
    output = {
        "total_tests": total_tests,
        "failures": total_failures,
        "time_seconds": elapsed,
        "procedural_scores": {k: {"avg": sum(v)/len(v), "min": min(v), "max": max(v)}
                              for k, v in proc_scores.items() if v},
        "type_distribution": proc_types,
    }
    with open("outputs/test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to outputs/test_results.json")

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    import os
    os.makedirs("outputs", exist_ok=True)
    sys.exit(main())
