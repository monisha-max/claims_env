"""
Inference Script — Insurance Claims Adjudication Environment
=============================================================
Runs a baseline LLM agent against all 3 tasks (easy, medium, hard)
and reports scores.

MANDATORY:
- Before submitting, ensure the following variables are defined in your
  environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

- The inference script must be named `inference.py` and placed in the
  root directory of the project.
- Participants must use OpenAI Client for all LLM calls using above
  variables.
"""

import json
import os
import re
import textwrap
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from openai import OpenAI

try:
    from claims_env.models import ClaimsAction
except ImportError:
    from models import ClaimsAction

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
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


def build_user_prompt(
    step: int,
    observation: Any,
    history: List[str],
    is_reset: bool = False,
) -> str:
    """Build the user prompt from the current observation."""
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


def parse_action(response_text: str) -> Optional[Dict[str, Any]]:
    """Extract a JSON action from the model's response."""
    if not response_text:
        return None

    # Try to find JSON in the response
    # First try: direct parse
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Second try: find JSON block in markdown
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Third try: find any JSON object
    json_match = re.search(r"\{[^{}]*\}", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def action_from_dict(d: Dict[str, Any]) -> ClaimsAction:
    """Convert a dict to a ClaimsAction, filtering unknown fields."""
    valid_fields = set(ClaimsAction.model_fields.keys())
    filtered = {k: v for k, v in d.items() if k in valid_fields}
    return ClaimsAction(**filtered)


def run_task(client: OpenAI, env, task_id: str) -> Dict[str, Any]:
    """Run a single task and return the result."""
    print(f"[START] task_id={task_id}")

    result = env.reset(task_id=task_id)
    observation = result
    history: List[str] = []

    print(f"[START] difficulty={observation.task_difficulty} max_steps={observation.max_steps}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": build_user_prompt(1, observation, history, is_reset=True),
        },
    ]

    final_score = 0.0
    steps_used = 0

    for step in range(1, MAX_STEPS + 1):
        if result.done:
            print(f"[STEP] step={step - 1} status=done_early")
            break

        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                stream=False,
            )
            response_text = completion.choices[0].message.content or ""
        except Exception as exc:
            print(f"[STEP] step={step} status=model_error error={exc}")
            # Fallback: issue a deny decision
            response_text = json.dumps({
                "action_type": "issue_decision",
                "decision": "deny",
                "decision_amount": 0,
                "decision_reasoning": "Unable to complete analysis due to error",
            })

        action_dict = parse_action(response_text)
        if action_dict is None:
            print(f"[STEP] step={step} status=parse_failed")
            messages.append({"role": "assistant", "content": response_text})
            messages.append({
                "role": "user",
                "content": "Invalid response. Please respond with a single JSON action object.",
            })
            continue

        try:
            action = action_from_dict(action_dict)
        except Exception as exc:
            print(f"[STEP] step={step} status=invalid_action error={exc}")
            messages.append({"role": "assistant", "content": response_text})
            messages.append({
                "role": "user",
                "content": f"Invalid action: {exc}. Please try again with valid parameters.",
            })
            continue

        result = env.step(action)
        observation = result
        steps_used = step
        history.append(action.action_type)

        reward = result.reward or 0.0
        print(
            f"[STEP] step={step} action={action.action_type} "
            f"reward={reward:+.3f} score={observation.current_score:.3f} "
            f"done={result.done}"
        )

        final_score = observation.current_score

        # Add to conversation
        messages.append({"role": "assistant", "content": response_text})
        messages.append({
            "role": "user",
            "content": build_user_prompt(step + 1, observation, history),
        })

        if result.done:
            break

    # If not done, force a decision
    if not result.done:
        print(f"[STEP] step={steps_used + 1} action=issue_decision status=forced_max_steps")
        fallback_action = ClaimsAction(
            action_type="issue_decision",
            decision="deny",
            decision_amount=0,
            decision_reasoning="Max steps reached, defaulting to deny",
        )
        result = env.step(fallback_action)
        final_score = result.current_score
        steps_used += 1

    score_breakdown = result.score_breakdown or {}
    print(
        f"[END] task_id={task_id} score={final_score:.3f} "
        f"steps={steps_used} breakdown={json.dumps(score_breakdown)}"
    )

    return {
        "task_id": task_id,
        "score": final_score,
        "steps_used": steps_used,
        "score_breakdown": score_breakdown,
    }


def main() -> None:
    """Run baseline inference on all tasks."""
    print(f"[START] Insurance Claims Adjudication — Baseline Inference")
    print(f"[START] model={MODEL_NAME} api={API_BASE_URL} max_steps={MAX_STEPS}")

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Use the environment directly (no server needed for inference)
    try:
        from claims_env.server.claims_env_environment import ClaimsEnvironment
    except ImportError:
        from server.claims_env_environment import ClaimsEnvironment

    env = ClaimsEnvironment()

    results = []
    start_time = time.time()

    for task_id in TASK_IDS:
        task_result = run_task(llm_client, env, task_id)
        results.append(task_result)

    elapsed = time.time() - start_time

    # Summary
    total_score = 0.0
    for r in results:
        total_score += r["score"]
    avg_score = total_score / len(results) if results else 0
    print(f"[END] average_score={avg_score:.3f} total_time={elapsed:.1f}s tasks={len(results)}")

    # Save results
    output = {
        "model": MODEL_NAME,
        "api_base_url": API_BASE_URL,
        "max_steps": MAX_STEPS,
        "results": results,
        "average_score": avg_score,
        "total_time_seconds": elapsed,
    }

    os.makedirs("outputs", exist_ok=True)
    output_path = "outputs/inference_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to {output_path}")


if __name__ == "__main__":
    main()
