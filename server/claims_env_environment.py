"""
Insurance Claims Adjudication Environment Implementation.

The agent processes insurance claims through a multi-step workflow:
verify eligibility, check coverage, identify exclusions, calculate
payouts, detect fraud, and issue decisions. Each step is graded
against deterministic ground truth derived from the policy document.
"""

import math
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import ClaimsAction, ClaimsObservation, ClaimsState
except ImportError:
    from models import ClaimsAction, ClaimsObservation, ClaimsState

try:
    from .tasks.task_definitions import TASKS, get_task
except ImportError:
    from server.tasks.task_definitions import TASKS, get_task

try:
    from .generator.scenario_generator import ScenarioGenerator
except ImportError:
    from server.generator.scenario_generator import ScenarioGenerator


class ClaimsEnvironment(Environment):
    """
    Insurance Claims Adjudication environment.

    The agent reads policy documents, claim submissions, and supporting
    evidence, then takes actions to adjudicate the claim. Each action is
    scored against deterministic ground truth.

    Episodes are multi-step: the agent performs multiple actions
    (check eligibility, check coverage, calculate payout, etc.)
    before issuing a final decision. Reward is provided at each step.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = ClaimsState(episode_id=str(uuid4()), step_count=0)
        self._task: Optional[Dict[str, Any]] = None
        self._ground_truth: Optional[Dict[str, Any]] = None
        self._scores: Dict[str, float] = {}
        self._actions_taken: List[str] = []
        self._fraud_flags_found: List[str] = []
        self._max_steps: int = 20
        self._decision_issued: bool = False
        self._request_info_rewarded: bool = False

    def reset(
        self,
        task_id: Optional[str] = None,
        episode_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        insurance_type: Optional[str] = None,
        seed: Optional[int] = None,
        **kwargs,
    ) -> ClaimsObservation:
        """Reset with a fixed task or generate a procedural scenario.

        Fixed tasks:   reset(task_id="easy_auto_collision")
        Procedural:    reset(difficulty="medium", insurance_type="auto", seed=42)
        Random:        reset(difficulty="hard")  # random type and seed
        Default:       reset()  # easy_auto_collision
        """
        if difficulty is not None or seed is not None:
            # Procedural generation mode
            gen = ScenarioGenerator(
                seed=seed,
                difficulty=difficulty or "medium",
                insurance_type=insurance_type,
            )
            self._task = gen.generate()
            task_id = self._task["task_id"]
        elif task_id is None:
            task_id = "easy_auto_collision"
            self._task = get_task(task_id)
        else:
            self._task = get_task(task_id)
        self._ground_truth = self._task["ground_truth"]
        self._scores = {}
        self._actions_taken = []
        self._fraud_flags_found = []
        self._max_steps = self._task.get("max_steps", 20)
        self._decision_issued = False
        self._request_info_rewarded = False

        self._state = ClaimsState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=task_id,
            task_difficulty=self._task["difficulty"],
            actions_taken=[],
            current_score=0.0,
            eligibility_checked=False,
            coverage_checked=False,
            payout_calculated=False,
            decision_issued=False,
            fraud_flags=[],
        )

        return ClaimsObservation(
            task_id=task_id,
            task_difficulty=self._task["difficulty"],
            policy_document=self._task["policy_document"],
            claim_submission=self._task["claim_submission"],
            supporting_evidence=self._task["supporting_evidence"],
            action_result="Environment reset. Read the policy and claim, then begin adjudication.",
            action_success=True,
            score_breakdown={},
            current_score=0.001,
            steps_taken=0,
            max_steps=self._max_steps,
            done=False,
            reward=0.001,
        )

    def step(self, action: ClaimsAction) -> ClaimsObservation:  # type: ignore[override]
        """Execute one adjudication action and return graded observation."""
        self._state.step_count += 1
        self._actions_taken.append(action.action_type)
        self._state.actions_taken = self._actions_taken.copy()

        # Check if episode already ended
        if self._decision_issued:
            return self._make_observation(
                "Decision already issued. Episode is complete.",
                success=False,
                done=True,
                reward=-0.05,
            )

        # Check step limit
        if self._state.step_count > self._max_steps:
            return self._make_observation(
                f"Maximum steps ({self._max_steps}) reached without issuing a decision.",
                success=False,
                done=True,
                reward=-0.1,
            )

        # Dispatch to handler
        handlers = {
            "check_eligibility": self._handle_check_eligibility,
            "check_coverage": self._handle_check_coverage,
            "check_exclusion": self._handle_check_exclusion,
            "calculate_payout": self._handle_calculate_payout,
            "flag_fraud": self._handle_flag_fraud,
            "request_info": self._handle_request_info,
            "issue_decision": self._handle_issue_decision,
        }

        handler = handlers.get(action.action_type)
        if handler is None:
            return self._make_observation(
                f"Unknown action type: {action.action_type}",
                success=False,
                done=False,
                reward=-0.05,
            )

        return handler(action)

    @property
    def state(self) -> ClaimsState:
        return self._state

    # --- Action Handlers ---

    def _handle_check_eligibility(self, action: ClaimsAction) -> ClaimsObservation:
        gt = self._ground_truth["eligibility"]
        self._state.eligibility_checked = True

        # The agent gets credit for performing this step
        # We give full marks since the key info is in the observation
        score = 0.0
        result_text = (
            f"Eligibility check complete.\n"
            f"Policy ID: {action.policy_id or 'N/A'}\n"
            f"Incident Date: {action.incident_date or 'N/A'}\n"
            f"Result: Policyholder {'IS' if gt['is_eligible'] else 'IS NOT'} eligible.\n"
            f"Details: {gt['reason']}"
        )

        # Award points for checking eligibility
        if "eligibility" not in self._scores:
            weight = self._task["scoring_weights"]["eligibility"]
            score = weight
            self._scores["eligibility"] = score

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_check_coverage(self, action: ClaimsAction) -> ClaimsObservation:
        gt = self._ground_truth["coverage"]
        self._state.coverage_checked = True

        section = action.policy_section or ""
        claim_item = action.claim_item or ""

        result_text = (
            f"Coverage check for section '{section}', item '{claim_item}'.\n"
            f"Primary coverage section: {gt['section']}.\n"
            f"Coverage determination: {'COVERED' if gt['is_covered'] else 'NOT COVERED'}.\n"
            f"Reason: {gt['reason']}"
        )

        # If item-level coverage info exists, provide details
        if "item_coverage" in gt and claim_item:
            item_key = self._fuzzy_match_item(claim_item, gt["item_coverage"])
            if item_key:
                item_info = gt["item_coverage"][item_key]
                covered = item_info.get("covered", False)
                result_text += f"\n\nItem '{item_key}': {'COVERED' if covered else 'NOT COVERED'}"
                if "rate" in item_info:
                    result_text += f" at {item_info['rate']*100:.0f}%"
                if "reason" in item_info:
                    result_text += f"\nReason: {item_info['reason']}"
                if "copay" in item_info:
                    result_text += f"\nCopay: ${item_info['copay']}"

        # Score: partial credit for each coverage check
        score = 0.0
        if "coverage" not in self._scores:
            weight = self._task["scoring_weights"]["coverage"]
            self._scores["coverage"] = weight * 0.5  # first check gets half
            score = weight * 0.5
        elif self._scores["coverage"] < self._task["scoring_weights"]["coverage"]:
            increment = self._task["scoring_weights"]["coverage"] * 0.1
            self._scores["coverage"] = min(
                self._scores["coverage"] + increment,
                self._task["scoring_weights"]["coverage"],
            )
            score = increment

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_check_exclusion(self, action: ClaimsAction) -> ClaimsObservation:
        gt = self._ground_truth["exclusions"]

        section = action.policy_section or ""
        claim_item = action.claim_item or ""

        applicable = gt["applicable_exclusions"]
        result_text = f"Exclusion check for section '{section}', item '{claim_item}'.\n"

        if not gt["any_apply"]:
            result_text += "No exclusions apply to this claim."
        else:
            result_text += f"Found {len(applicable)} applicable exclusion(s):\n"
            for exc in applicable:
                result_text += f"  - {exc['item']}: {exc['exclusion']} (${exc['amount_excluded']:,.2f})\n"

        score = 0.0
        if "exclusions" not in self._scores:
            weight = self._task["scoring_weights"]["exclusions"]
            self._scores["exclusions"] = weight
            score = weight

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_calculate_payout(self, action: ClaimsAction) -> ClaimsObservation:
        gt = self._ground_truth["payout"]
        self._state.payout_calculated = True

        claimed = action.claimed_amount or 0
        deductible = action.deductible or 0
        limit = action.coverage_limit or 0
        rate = action.coverage_rate or 0

        # Calculate what the agent proposed
        if rate > 0 and limit > 0:
            agent_payout = min(max(claimed - deductible, 0) * rate, limit)
        elif rate > 0:
            agent_payout = max(claimed - deductible, 0) * rate
        else:
            agent_payout = max(claimed - deductible, 0)

        correct_payout = gt["correct_payout"]

        # Score based on how close the agent's calculation is
        if correct_payout == 0:
            # If correct is 0 (denial), agent gets full marks for proposing 0
            payout_accuracy = 1.0 if agent_payout == 0 else max(0, 1.0 - abs(agent_payout) / 10000)
        else:
            error_ratio = abs(agent_payout - correct_payout) / correct_payout
            payout_accuracy = max(0.0, 1.0 - error_ratio)

        weight = self._task["scoring_weights"]["payout"]
        score = weight * payout_accuracy
        self._scores["payout"] = score

        result_text = (
            f"Payout calculation recorded.\n"
            f"  Calculated payout: ${agent_payout:,.2f}\n"
            f"  Claimed: ${claimed:,.2f} | Deductible: ${deductible:,.2f} "
            f"| Limit: ${limit:,.2f} | Rate: {rate*100:.0f}%"
        )

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_flag_fraud(self, action: ClaimsAction) -> ClaimsObservation:
        gt_flags = self._ground_truth.get("fraud_flags", [])
        indicator = (action.fraud_indicator or "").strip()
        evidence = (action.fraud_evidence or "").strip()

        # Reject blank flag_fraud calls — must provide substantive indicator text
        if not indicator and not evidence:
            return self._make_observation(
                "Fraud flag rejected: fraud_indicator and fraud_evidence cannot both be empty.",
                success=False,
                done=False,
                reward=-0.05,
            )

        # Check if this flag matches any ground truth fraud indicator
        matched = False
        matched_flag = None
        for flag in gt_flags:
            if self._fuzzy_match_fraud(indicator, evidence, flag):
                if flag["indicator"] not in self._fraud_flags_found:
                    matched = True
                    matched_flag = flag
                    self._fraud_flags_found.append(flag["indicator"])
                    self._state.fraud_flags = self._fraud_flags_found.copy()
                    break

        weight = self._task["scoring_weights"]["fraud"]
        score = 0.0

        if not gt_flags:
            # No fraud expected — penalize false positive slightly
            if indicator:
                score = -0.02
                result_text = (
                    f"Fraud flag '{indicator}' noted. "
                    "However, no fraud indicators exist for this claim. "
                    "False fraud flags reduce score."
                )
            else:
                result_text = "No fraud indicators to check for this claim."
        elif matched and matched_flag:
            # Correct fraud flag — award proportional score
            per_flag_score = weight / len(gt_flags)
            score = per_flag_score
            self._scores["fraud"] = self._scores.get("fraud", 0) + per_flag_score
            result_text = (
                f"FRAUD FLAG CONFIRMED: '{matched_flag['indicator']}'\n"
                f"Severity: {matched_flag['severity']}\n"
                f"Details: {matched_flag['description']}\n"
                f"Fraud flags found: {len(self._fraud_flags_found)}/{len(gt_flags)}"
            )
        else:
            score = -0.01  # Small penalty for unmatched flag
            result_text = (
                f"Fraud flag '{indicator}' not matched to known indicators. "
                f"Fraud flags found so far: {len(self._fraud_flags_found)}/{len(gt_flags)}"
            )

        return self._make_observation(result_text, success=matched, done=False, reward=score)

    def _handle_request_info(self, action: ClaimsAction) -> ClaimsObservation:
        """Handle information request — provides contextual response."""
        question = (action.info_question or "").strip()

        # Provide relevant information based on the question
        result_text = (
            f"Information request: '{question}'\n\n"
            "Refer to the policy document and supporting evidence provided. "
            "All available information has been included in the initial observation."
        )

        # Reward once per episode for a non-empty question; zero thereafter
        if question and not self._request_info_rewarded:
            score = 0.01
            self._request_info_rewarded = True
        else:
            score = 0.0

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_issue_decision(self, action: ClaimsAction) -> ClaimsObservation:
        """Handle final decision — grades and ends the episode."""
        self._decision_issued = True
        self._state.decision_issued = True

        gt = self._ground_truth
        agent_decision = action.decision or ""
        agent_amount = action.decision_amount or 0.0
        agent_reasoning = action.decision_reasoning or ""

        correct_decision = gt["correct_decision"]
        correct_amount = gt["correct_decision_amount"]

        weight = self._task["scoring_weights"]["decision"]

        # Score the decision
        decision_score = 0.0

        # Decision type match (approve/deny/partial_approve)
        if agent_decision == correct_decision:
            decision_score += 0.6
        elif (agent_decision in ("approve", "partial_approve") and
              correct_decision in ("approve", "partial_approve")):
            decision_score += 0.3  # Partial credit for close
        # deny vs approve = 0

        # Amount accuracy (for approve/partial_approve)
        if correct_amount > 0:
            error_ratio = abs(agent_amount - correct_amount) / correct_amount
            amount_accuracy = max(0.0, 1.0 - error_ratio)
            decision_score += 0.3 * amount_accuracy
        elif correct_amount == 0:
            # Denial — full marks if agent amount is 0
            decision_score += 0.3 if agent_amount == 0 else 0.0

        # Reasoning bonus (0.1 if reasoning is provided)
        if agent_reasoning and len(agent_reasoning) > 20:
            decision_score += 0.1

        decision_score = min(decision_score, 1.0)
        score = weight * decision_score
        self._scores["decision"] = score

        total_score = self._clamp_score(sum(self._scores.values()))
        self._state.current_score = total_score

        result_text = (
            f"DECISION ISSUED: {agent_decision.upper()}\n"
            f"Amount: ${agent_amount:,.2f}\n"
            f"Reasoning: {agent_reasoning}\n\n"
            f"--- GRADING ---\n"
            f"Correct decision: {correct_decision.upper()}\n"
            f"Correct amount: ${correct_amount:,.2f}\n"
            f"Decision score: {decision_score*100:.1f}%\n\n"
            f"--- FINAL SCORE BREAKDOWN ---\n"
        )
        for category, s in sorted(self._scores.items()):
            w = self._task["scoring_weights"].get(category, 0)
            result_text += f"  {category}: {s:.3f} / {w:.3f}\n"
        result_text += f"\nTOTAL SCORE: {total_score:.3f} / 1.000"

        return self._make_observation(
            result_text,
            success=(agent_decision == correct_decision),
            done=True,
            reward=score,
        )

    # --- Helpers ---

    @staticmethod
    def _clamp_score(value: float) -> float:
        """Clamp to strictly between 0 and 1 (validator rejects exact 0.0 or 1.0)."""
        return min(0.999, max(0.001, value))

    def _make_observation(
        self, result: str, success: bool, done: bool, reward: float
    ) -> ClaimsObservation:
        total_score = sum(self._scores.values())
        total_score = self._clamp_score(total_score)
        reward = self._clamp_score(reward)
        self._state.current_score = total_score

        return ClaimsObservation(
            task_id=self._task["task_id"] if self._task else None,
            task_difficulty=self._task["difficulty"] if self._task else None,
            policy_document=None,  # Only sent on reset to save bandwidth
            claim_submission=None,
            supporting_evidence=None,
            action_result=result,
            action_success=success,
            score_breakdown=dict(self._scores),
            current_score=total_score,
            steps_taken=self._state.step_count,
            max_steps=self._max_steps,
            done=done,
            reward=reward,
        )

    def _fuzzy_match_item(self, query: str, items: Dict[str, Any]) -> Optional[str]:
        """Fuzzy match a claim item query to ground truth item keys."""
        query_lower = query.lower().strip()
        for key in items:
            if key in query_lower or query_lower in key:
                return key
        # Try partial matches
        for key in items:
            key_words = set(key.replace("_", " ").split())
            query_words = set(query_lower.replace("_", " ").split())
            if key_words & query_words:
                return key
        return None

    def _fuzzy_match_fraud(
        self, indicator: str, evidence: str, gt_flag: Dict[str, Any]
    ) -> bool:
        """Check if agent's fraud flag matches a ground truth indicator."""
        ind_lower = indicator.lower().strip()
        ev_lower = evidence.lower().strip()
        gt_ind = gt_flag["indicator"].lower()
        gt_desc = gt_flag["description"].lower()

        # Reject empty indicators — empty string is a substring of everything
        if not ind_lower and not ev_lower:
            return False

        # Direct indicator match (require non-empty ind_lower to avoid trivial matches)
        if ind_lower and (gt_ind in ind_lower or ind_lower in gt_ind):
            return True

        # Check key terms from description
        combined = ind_lower + " " + ev_lower
        key_terms = {
            "timing": ["timing", "inception", "18 days", "new policy", "recently"],
            "inflated_values": ["inflat", "overstat", "receipt", "actual price", "higher than"],
            "related_contractor": ["contractor", "jameson", "related", "surname", "conflict"],
            "prior_claims": ["prior", "previous", "history", "pattern", "multiple claims"],
            "items_moved": ["moved", "boxes", "van", "loading", "storage", "neighbor"],
            "suspicious_fire": ["fire", "burn pattern", "unusual", "arson", "suspicious"],
            "no_receipts": ["receipt", "no proof", "undocumented", "unverif"],
            "no_alarm": ["alarm", "security", "no security"],
        }

        if gt_ind in key_terms:
            for term in key_terms[gt_ind]:
                if term in combined:
                    return True

        return False
