"""
Inference Script — Insurance Claims Adjudication Environment
=============================================================
MANDATORY:
- Before submitting, ensure the following variables are defined:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
- The inference script must be named `inference.py` and placed in the root.
- Participants must use OpenAI Client for all LLM calls.

STDOUT FORMAT:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import json
import math
import os
import re
import sys
import textwrap
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

try:
    from claims_env.models import ClaimsAction
except ImportError:
    try:
        from models import ClaimsAction
    except ImportError:
        sys.path.insert(0, os.path.dirname(__file__))
        from models import ClaimsAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = "claims_env"
MAX_STEPS = 12
TEMPERATURE = 0.1
MAX_TOKENS = 1024

TASK_IDS = [
    "easy_auto_collision",
    "easy_travel_cancellation",
    "medium_medical_exclusions",
    "medium_pet_surgery",
    "medium_life_benefit",
    "medium_liability_injury",
    "hard_property_fraud",
    "hard_flood_exclusion",
    "hard_disability_claim",
]

SYSTEM_PROMPT = textwrap.dedent("""\
You are an expert insurance claims adjuster. You process insurance claims
by reading policy documents, verifying eligibility, checking coverage,
identifying exclusions, calculating payouts, detecting fraud, and issuing
decisions.

You interact with a claims adjudication environment using structured actions.
Each action must be a valid JSON object with an "action_type" field.

Available action types:
1. check_eligibility — Verify policyholder eligibility
   {"action_type": "check_eligibility", "policy_id": "...", "incident_date": "YYYY-MM-DD"}

2. check_coverage — Check if a claim item is covered
   {"action_type": "check_coverage", "policy_section": "...", "claim_item": "..."}

3. check_exclusion — Check for applicable exclusions
   {"action_type": "check_exclusion", "policy_section": "...", "claim_item": "..."}

4. calculate_payout — Calculate the payout amount
   {"action_type": "calculate_payout", "claimed_amount": 0.0, "deductible": 0.0, "coverage_limit": 0.0, "coverage_rate": 0.0}

5. flag_fraud — Flag a potential fraud indicator
   {"action_type": "flag_fraud", "fraud_indicator": "...", "fraud_evidence": "..."}

6. issue_decision — Issue final decision (MUST be your last action)
   {"action_type": "issue_decision", "decision": "approve|deny|partial_approve", "decision_amount": 0.0, "decision_reasoning": "..."}

WORKFLOW:
1. Read the policy document and claim carefully
2. Check eligibility first
3. Check coverage for relevant items/sections
4. Check for exclusions
5. Calculate the correct payout
6. If you see fraud indicators, flag them BEFORE your decision
7. Issue your final decision last

RESPOND WITH ONLY A SINGLE JSON ACTION. No explanation text.
""").strip()


def safe_score(raw: Any) -> float:
    """Map any raw score to strict open interval (0.01, 0.99)."""
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return 0.01
    if not math.isfinite(v):
        return 0.01
    v = max(0.0, min(1.0, v))
    return round(v * 0.98 + 0.01, 4)


# ─── Logging helpers (exact format required by validator) ────────────

def log_start(task: str) -> None:
    print(f"[START] task={task} env={BENCHMARK} model={MODEL_NAME}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str] = None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    print(f"[END] success={success_val} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


# ─── Prompt / parse helpers ──────────────────────────────────────────

def build_user_prompt(step, observation, history, is_reset=False):
    parts = [f"Step {step} of {MAX_STEPS}"]
    if is_reset and observation.policy_document:
        parts.append(f"\n=== POLICY DOCUMENT ===\n{observation.policy_document}")
        parts.append(f"\n=== CLAIM SUBMISSION ===\n{observation.claim_submission}")
        if observation.supporting_evidence:
            parts.append("\n=== SUPPORTING EVIDENCE ===")
            for i, ev in enumerate(observation.supporting_evidence, 1):
                parts.append(f"{i}. {ev}")
        parts.append(f"\nTask: {observation.task_id} (Difficulty: {observation.task_difficulty})")
    if observation.action_result and not is_reset:
        parts.append(f"\n=== RESULT OF LAST ACTION ===\n{observation.action_result}")
    if observation.score_breakdown:
        parts.append(f"\nCurrent score: {observation.current_score:.3f}")
    if history:
        parts.append(f"\nPrevious actions: {', '.join(history[-5:])}")
    parts.append("\nRespond with a single JSON action object.")
    return "\n".join(parts)


def parse_action(response_text):
    if not response_text:
        return None
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    m = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def action_from_dict(d):
    valid_fields = set(ClaimsAction.model_fields.keys())
    filtered = {k: v for k, v in d.items() if k in valid_fields}
    return ClaimsAction(**filtered)


# ─── Main task runner ────────────────────────────────────────────────

def run_task(client, env, task_id):
    log_start(task=task_id)

    result = env.reset(task_id=task_id)
    observation = result
    history = []
    rewards = []
    steps_used = 0
    score = 0.01

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(1, observation, history, is_reset=True)},
    ]

    for step in range(1, MAX_STEPS + 1):
        if result.done:
            break

        # Get LLM response
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception:
            response_text = json.dumps({
                "action_type": "issue_decision",
                "decision": "deny",
                "decision_amount": 0,
                "decision_reasoning": "Unable to complete analysis due to error",
            })

        # Parse action
        action_dict = parse_action(response_text)
        if action_dict is None:
            log_step(step=step, action="parse_error", reward=0.01, done=False, error="Failed to parse JSON")
            rewards.append(0.01)
            steps_used = step
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Invalid response. Please respond with a single JSON action object."})
            continue

        try:
            action = action_from_dict(action_dict)
        except Exception as exc:
            log_step(step=step, action="invalid_action", reward=0.01, done=False, error=str(exc)[:100])
            rewards.append(0.01)
            steps_used = step
            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": "Invalid action. Please try again."})
            continue

        # Execute step
        try:
            result = env.step(action)
            observation = result
            steps_used = step

            reward = safe_score(result.reward) if result.reward is not None else 0.01
            done = bool(result.done)
            rewards.append(reward)
            history.append(action.action_type)
            score = safe_score(observation.current_score)

            log_step(step=step, action=action.action_type, reward=reward, done=done, error=None)

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": build_user_prompt(step + 1, observation, history)})

            if done:
                break
        except Exception as exc:
            log_step(step=step, action=action.action_type, reward=0.01, done=True, error=str(exc)[:100])
            rewards.append(0.01)
            steps_used = step
            break

    # Force decision if not done
    if not result.done:
        steps_used += 1
        try:
            fallback = ClaimsAction(
                action_type="issue_decision", decision="deny",
                decision_amount=0, decision_reasoning="Max steps reached",
            )
            result = env.step(fallback)
            reward = safe_score(result.reward) if result.reward is not None else 0.01
            rewards.append(reward)
            score = safe_score(result.current_score)
            log_step(step=steps_used, action="issue_decision", reward=reward, done=True, error=None)
        except Exception:
            rewards.append(0.01)

    success = score > 0.1
    log_end(success=success, steps=steps_used, score=score, rewards=rewards)

    return {"task_id": task_id, "score": score, "steps_used": steps_used}


def main():
    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    try:
        from claims_env.server.claims_env_environment import ClaimsEnvironment
    except ImportError:
        from server.claims_env_environment import ClaimsEnvironment

    env = ClaimsEnvironment()
    results = []
    start_time = time.time()

    for task_id in TASK_IDS:
        try:
            task_result = run_task(llm_client, env, task_id)
        except Exception:
            log_start(task=task_id)
            log_end(success=False, steps=0, score=0.01, rewards=[0.01])
            task_result = {"task_id": task_id, "score": 0.01, "steps_used": 0}
        results.append(task_result)

    elapsed = time.time() - start_time
    avg_score = safe_score(sum(r["score"] for r in results) / len(results)) if results else 0.01

    os.makedirs("outputs", exist_ok=True)
    with open("outputs/inference_results.json", "w") as f:
        json.dump({"model": MODEL_NAME, "results": results, "average_score": avg_score, "time": elapsed}, f, indent=2)


if __name__ == "__main__":
    main()
