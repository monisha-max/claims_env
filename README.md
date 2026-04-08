---
title: Insurance Claims Adjudication Environment
emoji: 📋
colorFrom: blue
colorTo: green
sdk: docker
app_port: 8000
tags:
  - openenv
---

# Insurance Claims Adjudication Environment

An OpenEnv environment where AI agents process insurance claims by reading policy documents, verifying eligibility, checking coverage, calculating payouts, detecting fraud, and issuing decisions.

## Motivation

Insurance claims adjudication is one of the largest manual knowledge-work tasks in the world. In the United States alone, over $1.2 trillion in claims are processed annually. Each claim requires a human adjuster to read dense policy language, cross-reference it against claim details and supporting evidence, perform arithmetic to calculate payouts, and make a final coverage decision.

This environment captures that entire workflow as a structured, multi-step RL task. Every answer is derived deterministically from the policy document — no LLM judge needed, no subjectivity. The policy is both the input the agent reads and the answer key the grader checks against.

## How It Works

```
Agent                                       Environment
  |                                              |
  |  reset(task_id="easy_auto_collision")        |
  |--------------------------------------------->|
  |  Observation: policy + claim + evidence       |
  |<---------------------------------------------|
  |                                              |
  |  step(check_eligibility)                     |
  |--------------------------------------------->|
  |  Result + reward + score                     |
  |<---------------------------------------------|
  |                                              |
  |  step(check_coverage)                        |
  |--------------------------------------------->|
  |  ...                                         |
  |                                              |
  |  step(issue_decision, approve, $6400)        |
  |--------------------------------------------->|
  |  Final score: 0.825, done=True               |
  |<---------------------------------------------|
```

The agent follows a natural claims workflow: verify eligibility, check what is covered, identify exclusions, compute the payout, flag fraud if present, and issue a final decision. Each step is graded independently and provides immediate reward.

## Action Space

Seven action types, matching the real claims adjudication workflow:

| Action | Description | Key Parameters |
|--------|-------------|----------------|
| `check_eligibility` | Verify the policy is active and the claim is timely | `policy_id`, `incident_date` |
| `check_coverage` | Determine whether a specific item is covered | `policy_section`, `claim_item` |
| `check_exclusion` | Identify applicable policy exclusions | `policy_section`, `claim_item` |
| `calculate_payout` | Compute the payout using policy terms | `claimed_amount`, `deductible`, `coverage_limit`, `coverage_rate` |
| `flag_fraud` | Flag a suspected fraud indicator with evidence | `fraud_indicator`, `fraud_evidence` |
| `request_info` | Ask for additional information | `info_question` |
| `issue_decision` | Issue the final decision (ends the episode) | `decision`, `decision_amount`, `decision_reasoning` |

All actions are defined as typed Pydantic models in `models.py`.

## Observation Space

On `reset()`, the agent receives:

- **Policy document** -- full insurance policy text with sections, coverage rates, deductibles, limits, exclusions, and conditions
- **Claim submission** -- incident description, itemized charges, and total claimed amount
- **Supporting evidence** -- police reports, medical records, repair estimates, witness statements, and receipts

On each `step()`, the agent receives:

- **Action result** -- textual description of the outcome
- **Score breakdown** -- current score per grading category
- **Current score** -- cumulative score from 0.0 to 1.0
- **Steps remaining** -- how many steps are left before the episode ends

## Tasks

### 9 Fixed Benchmark Tasks Across 6 Insurance Domains

**Easy** -- straightforward claims with clear coverage, no tricks.

| Task ID | Domain | Scenario | Decision | Payout |
|---------|--------|----------|----------|--------|
| `easy_auto_collision` | Auto | Rear-end collision, clear coverage | Approve | $6,400 |
| `easy_travel_cancellation` | Travel | Flight cancellation with receipts | Approve | $4,480 |

**Medium** -- multiple coverage sections, exclusions, or complex arithmetic.

| Task ID | Domain | Scenario | Decision | Payout |
|---------|--------|----------|----------|--------|
| `medium_medical_exclusions` | Medical | Appendectomy with 10 line items, dental excluded | Partial approve | $26,215 |
| `medium_pet_surgery` | Pet | Surgery with pre-existing condition nuances | Approve | $5,120 |
| `medium_life_benefit` | Life | Death benefit with beneficiary verification | Approve | $500,000 |
| `medium_liability_injury` | Liability | Third-party injury, multiple damage categories | Approve | $51,090 |

**Hard** -- fraud detection, ambiguous policy language, or tricky exclusions.

| Task ID | Domain | Scenario | Decision | Payout |
|---------|--------|----------|----------|--------|
| `hard_property_fraud` | Home | Burglary with 8 fraud indicators | Deny | $0 |
| `hard_flood_exclusion` | Home/Flood | Flood damage with no flood rider | Deny | $0 |
| `hard_disability_claim` | Disability | Complex disability with partial coverage | Approve | $6,500 |

### Procedural Generation (Unlimited Scenarios)

Beyond the 9 fixed tasks, the environment generates unique scenarios on every reset using a seed-based procedural engine:

```python
# Fixed task (reproducible benchmark)
env.reset(task_id="easy_auto_collision")

# Procedural task (unique scenario, reproducible with seed)
env.reset(difficulty="medium", insurance_type="auto", seed=42)

# Fully random
env.reset(difficulty="hard")
```

The generator creates structured policy data first, then renders it as natural language. Ground truth is computed automatically from the structured data -- no human-authored answers. This means:

- Every seed produces a unique policy, claim, evidence set, and correct answer
- Same seed always produces the same scenario (reproducible)
- 4 insurance types (auto, medical, home, travel) x 3 difficulty levels
- Hard scenarios inject 4-7 fraud indicators from a pool of 12 types

## Scoring

Each task is graded from 0.0 to 1.0 across six categories. Weights vary by difficulty to reflect what matters most at each level:

| Category | What It Measures | Easy | Medium | Hard |
|----------|-----------------|------|--------|------|
| Eligibility | Policy active, claim timely | 10% | 10% | 5% |
| Coverage | Correct identification of covered items | 25% | 25% | 15% |
| Exclusions | Correct identification of excluded items | 10% | 15% | 15% |
| Payout | Accuracy of dollar amount calculation | 30% | 25% | 15% |
| Fraud | Detection of planted fraud indicators | 5% | 5% | 30% |
| Decision | Correct approve/deny with reasoning | 20% | 20% | 20% |

Key properties of the reward function:

- **Dense signal** -- reward at every step, not just end-of-episode
- **Partial credit** -- payout 90% correct earns proportional score, not zero
- **Penalties** -- false fraud flags (-0.02), empty fraud flags (-0.05), exceeding max steps (-0.1)
- **Deterministic** -- no LLM judge, no randomness in grading

## Baseline Scores

Model: Claude Sonnet 4 (Anthropic). Runtime: 141 seconds for all 9 tasks.

| Task | Score | Steps |
|------|-------|-------|
| easy_auto_collision | 0.825 | 5 |
| easy_travel_cancellation | 0.825 | 5 |
| medium_medical_exclusions | 0.862 | 9 |
| medium_pet_surgery | 0.825 | 5 |
| medium_life_benefit | 0.850 | 5 |
| medium_liability_injury | 0.850 | 6 |
| hard_property_fraud | 0.640 | 11 |
| hard_flood_exclusion | 0.600 | 5 |
| hard_disability_claim | 0.820 | 7 |
| **Average** | **0.789** | -- |

Difficulty progression is clear: easy tasks average 0.825, medium tasks average 0.847, and hard tasks average 0.687. The fraud detection task (hard_property_fraud) is the most challenging, with the agent identifying 4 of 8 planted fraud indicators.

## Setup

### Install from source

```bash
git clone https://github.com/monisha-max/claims_env
cd claims_env
uv sync
```

### Run the server locally

```bash
uv run server
```

The server starts at `http://localhost:8000` with endpoints: `/reset`, `/step`, `/state`, `/health`, `/ws`, `/schema`.

### Run with Docker

```bash
docker build -t claims-env:latest -f server/Dockerfile .
docker run -d -p 8000:8000 claims-env:latest
```

### Run inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token-here"

python inference.py
```

### Run tests

```bash
pytest tests/ -v
```

83 unit tests covering model validation, environment state management, grading accuracy, fraud detection, edge cases, procedural generation, and reproducibility.

## Usage

```python
from claims_env import ClaimsEnv, ClaimsAction

# Connect to a running server
with ClaimsEnv(base_url="http://localhost:8000").sync() as env:
    result = env.reset(task_id="easy_auto_collision")
    print(result.observation.policy_document)

    result = env.step(ClaimsAction(
        action_type="check_eligibility",
        policy_id="POL-2024-78432",
        incident_date="2024-03-15",
    ))
    print(result.observation.action_result)

    result = env.step(ClaimsAction(
        action_type="issue_decision",
        decision="approve",
        decision_amount=6400.00,
        decision_reasoning="Collision covered under Section 1, payout = (8500 - 500) * 0.80",
    ))
    print(f"Score: {result.observation.current_score}")
```

## Project Structure

```
claims_env/
├── models.py                      # Typed Pydantic models: ClaimsAction, ClaimsObservation, ClaimsState
├── client.py                      # WebSocket client (ClaimsEnv)
├── inference.py                   # Baseline inference script using OpenAI client
├── test_scenarios.py              # Stress test: 214 scenarios (perfect agent, random agent, reproducibility)
├── openenv.yaml                   # OpenEnv manifest
├── pyproject.toml                 # Package configuration
├── __init__.py
├── tests/
│   ├── test_models.py             # 13 tests: model validation and type safety
│   ├── test_environment.py        # 41 tests: reset, step, state, scoring, fraud, edge cases
│   └── test_procedural.py         # 29 tests: generation, reproducibility, integration
└── server/
    ├── app.py                     # FastAPI server via create_app()
    ├── claims_env_environment.py  # Environment logic and grading
    ├── Dockerfile
    ├── tasks/
    │   └── task_definitions.py    # 9 fixed benchmark tasks with ground truth
    └── generator/
        ├── scenario_generator.py  # Procedural scenario generation engine
        └── pools.py               # Names, exclusions, fraud indicators, claim templates
```
