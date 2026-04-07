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

## Why This Environment?

Insurance claims adjudication is a massive real-world task:
- **$1.2 trillion** in claims paid annually in the US alone
- Claims adjusters spend **hours** per claim reading dense policy language
- Errors cost insurers billions and delay payouts to legitimate claimants
- Fraud detection requires pattern recognition across multiple evidence sources

This environment turns the claims adjudication workflow into a structured RL task with **deterministic grading** — the policy document itself is the answer key.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AGENT (inference.py)                                   │
│                                                         │
│  1. Read policy + claim + evidence                      │
│  2. check_eligibility → check_coverage → check_exclusion│
│  3. calculate_payout                                    │
│  4. flag_fraud (if suspicious)                          │
│  5. issue_decision (approve / deny / partial_approve)   │
└─────────────┬───────────────────────────────────────────┘
              │  WebSocket / HTTP
┌─────────────▼───────────────────────────────────────────┐
│  ENVIRONMENT SERVER (FastAPI)                           │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │  ClaimsEnvironment                          │       │
│  │  ├── Task definitions (policy + claim + GT) │       │
│  │  ├── Action handlers (7 action types)       │       │
│  │  └── Graders (deterministic scoring)        │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Action Space

| Action | Description | Parameters |
|--------|-------------|------------|
| `check_eligibility` | Verify policyholder is eligible | `policy_id`, `incident_date` |
| `check_coverage` | Check if an item is covered | `policy_section`, `claim_item` |
| `check_exclusion` | Check for applicable exclusions | `policy_section`, `claim_item` |
| `calculate_payout` | Calculate the payout amount | `claimed_amount`, `deductible`, `coverage_limit`, `coverage_rate` |
| `flag_fraud` | Flag a potential fraud indicator | `fraud_indicator`, `fraud_evidence` |
| `request_info` | Request additional information | `info_question` |
| `issue_decision` | Issue final decision (ends episode) | `decision`, `decision_amount`, `decision_reasoning` |

## Observation Space

On `reset()`, the agent receives:
- **Policy document**: Full insurance policy text with coverage terms, limits, deductibles, exclusions, and conditions
- **Claim submission**: Incident description, itemized charges, claimed amounts
- **Supporting evidence**: Police reports, medical records, repair estimates, witness statements

On each `step()`, the agent receives:
- **Action result**: Outcome of the action taken
- **Score breakdown**: Current score by category
- **Current score**: Running total (0.0-1.0)

## Tasks

### Task 1: Easy - Auto Collision Claim
Simple rear-end collision. Clear policy, no exclusions, straightforward payout calculation.
- **Expected score**: 0.80-1.00

### Task 2: Medium - Medical Claim with Exclusions
Emergency appendectomy with 10 itemized charges. Some items covered, dental excluded. Agent must handle multiple coverage sections (inpatient, outpatient, prescriptions) with different rates and deductibles.
- **Expected score**: 0.50-0.85

### Task 3: Hard - Suspicious Property Claim with Fraud
Home burglary claim with 8 fraud indicators: suspicious timing (18 days post-inception), inflated values, related-party contractor, prior claims pattern, items moved before incident. Agent must detect fraud and deny the claim.
- **Expected score**: 0.30-0.60

## Scoring

Each task is scored from 0.0 to 1.0 across these categories:

| Category | Weight (Easy) | Weight (Medium) | Weight (Hard) |
|----------|---------------|-----------------|---------------|
| Eligibility | 10% | 10% | 5% |
| Coverage | 25% | 25% | 15% |
| Exclusions | 10% | 15% | 15% |
| Payout | 30% | 25% | 15% |
| Fraud | 5% | 5% | 30% |
| Decision | 20% | 20% | 20% |

All scoring is **deterministic** — no LLM judge needed. The policy document defines the correct answer for every category.

## Setup

### Install

```bash
pip install git+https://huggingface.co/spaces/<username>/claims-env
```

### Run Locally

```bash
git clone <repo-url>
cd claims_env
uv sync
uv run server
```

### Docker

```bash
docker build -t claims-env:latest -f server/Dockerfile .
docker run -d -p 8000:8000 claims-env:latest
```

### Run Inference

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="Qwen/Qwen2.5-72B-Instruct"
export HF_TOKEN="your-token-here"

python inference.py
```

## Usage

```python
from claims_env import ClaimsEnv, ClaimsAction

# Sync usage
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
        decision_reasoning="Collision covered, payout = (8500-500)*0.80",
    ))
    print(f"Score: {result.observation.current_score}")
```

## Baseline Scores

| Task | Score | Steps |
|------|-------|-------|
| easy_auto_collision | ~0.82 | 5 |
| medium_medical_exclusions | ~0.65 | 8 |
| hard_property_fraud | ~0.40 | 8 |
| **Average** | **~0.62** | - |

## Project Structure

```
claims_env/
├── models.py                      # ClaimsAction, ClaimsObservation, ClaimsState
├── client.py                      # ClaimsEnv (WebSocket client)
├── openenv.yaml                   # OpenEnv manifest
├── pyproject.toml                 # Package config
├── inference.py                   # Baseline inference script
├── __init__.py
└── server/
    ├── app.py                     # FastAPI server (create_app)
    ├── claims_env_environment.py  # Environment logic + graders
    ├── Dockerfile
    ├── __init__.py
    └── tasks/
        ├── __init__.py
        └── task_definitions.py    # 3 tasks with ground truth
```
