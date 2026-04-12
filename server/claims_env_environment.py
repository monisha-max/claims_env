"""
Insurance Claims Adjudication Environment Implementation.

The agent processes insurance claims through a multi-step workflow:
verify eligibility, check coverage, identify exclusions, calculate
payouts, detect fraud, and issue decisions. Each step is graded
against deterministic ground truth derived from the policy document.

Advanced grading features:
- Honeypot evidence: planted fake documents that penalize agents who fall for them
- Investigation order bonus: rewards following the logical adjudication workflow
- Efficiency bonus: rewards completing tasks in fewer steps
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


# Ideal investigation order — agents get bonus for following this
IDEAL_ORDER = [
    "check_eligibility",
    "check_coverage",
    "check_exclusion",
    "calculate_payout",
    "flag_fraud",
    "issue_decision",
]

# Honeypot penalty — applied when agent tags honeypot evidence as real
HONEYPOT_PENALTY = -0.15

# Efficiency bonus — awarded when agent finishes in fewer steps
EFFICIENCY_BONUS_THRESHOLD = 0.5  # must use <= 50% of max steps
EFFICIENCY_BONUS = 0.05

# Investigation order bonus
ORDER_BONUS = 0.05


class ClaimsEnvironment(Environment):
    """
    Insurance Claims Adjudication environment.

    The agent reads policy documents, claim submissions, and supporting
    evidence, then takes actions to adjudicate the claim. Each action is
    scored against deterministic ground truth.

    Grading features:
    - Per-action scoring with partial credit
    - Honeypot evidence traps (planted fake documents that penalize)
    - Investigation order bonus (following logical workflow)
    - Efficiency bonus (completing in fewer steps)
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = ClaimsState(episode_id=str(uuid4()), step_count=0)
        self._task: Optional[Dict[str, Any]] = None
        self._ground_truth: Optional[Dict[str, Any]] = None
        self._scores: Dict[str, float] = {}
        self._actions_taken: List[str] = []
        self._fraud_flags_found: List[str] = []
        self._honeypots_triggered: List[str] = []
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
        curriculum_level: Optional[int] = None,
        **kwargs,
    ) -> ClaimsObservation:
        """Reset with a fixed task, procedural scenario, or curriculum level.

        Fixed tasks:      reset(task_id="easy_auto_collision")
        Procedural:       reset(difficulty="medium", insurance_type="auto", seed=42)
        Curriculum:       reset(curriculum_level=5, seed=42)
        Random:           reset(difficulty="hard")
        Default:          reset()  # easy_auto_collision

        Curriculum levels 1-10:
          1-3: easy (simple policies, no fraud, no honeypots)
          4-6: medium (exclusions, multiple sections)
          7-9: hard (fraud detection, honeypots, ambiguity)
          10:  adversarial (contradictory evidence, max honeypots)
        """
        if curriculum_level is not None:
            # Map curriculum level to difficulty
            if curriculum_level <= 3:
                difficulty = "easy"
            elif curriculum_level <= 6:
                difficulty = "medium"
            else:
                difficulty = "hard"
        if difficulty is not None or seed is not None:
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
        self._honeypots_triggered = []
        self._max_steps = self._task.get("max_steps", 20)
        self._decision_issued = False
        self._request_info_rewarded = False

        self._state = ClaimsState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=task_id,
            task_difficulty=self._task["difficulty"],
            actions_taken=[],
            current_score=0.001,
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

        if self._task is None or self._ground_truth is None:
            return self._make_observation(
                "Environment not initialized. Call reset(...) before step(...).",
                success=False, done=True, reward=0.001,
            )

        if self._decision_issued:
            return self._make_observation(
                "Decision already issued. Episode is complete.",
                success=False, done=True, reward=-0.05,
            )

        if self._state.step_count > self._max_steps:
            return self._make_observation(
                f"Maximum steps ({self._max_steps}) reached without issuing a decision.",
                success=False, done=True, reward=-0.1,
            )

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
                success=False, done=False, reward=-0.05,
            )

        return handler(action)

    @property
    def state(self) -> ClaimsState:
        return self._state

    # --- Action Handlers ---

    def _handle_check_eligibility(self, action: ClaimsAction) -> ClaimsObservation:
        gt = self._ground_truth["eligibility"]
        self._state.eligibility_checked = True

        score = 0.0
        result_text = (
            f"Eligibility check complete.\n"
            f"Policy ID: {action.policy_id or 'N/A'}\n"
            f"Incident Date: {action.incident_date or 'N/A'}\n"
            f"Result: Policyholder {'IS' if gt['is_eligible'] else 'IS NOT'} eligible.\n"
            f"Details: {gt['reason']}"
        )

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

                # Check for honeypot items
                if item_info.get("is_honeypot"):
                    self._honeypots_triggered.append(item_key)
                    result_text += "\n\n[WARNING: This item contains misleading information]"

        score = 0.0
        if "coverage" not in self._scores:
            weight = self._task["scoring_weights"]["coverage"]
            self._scores["coverage"] = weight * 0.5
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

        if rate > 0 and limit > 0:
            agent_payout = min(max(claimed - deductible, 0) * rate, limit)
        elif rate > 0:
            agent_payout = max(claimed - deductible, 0) * rate
        else:
            agent_payout = max(claimed - deductible, 0)

        correct_payout = gt["correct_payout"]

        if correct_payout == 0:
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
        honeypots = self._ground_truth.get("honeypots", [])
        indicator = (action.fraud_indicator or "").strip()
        evidence = (action.fraud_evidence or "").strip()

        if not indicator and not evidence:
            return self._make_observation(
                "Fraud flag rejected: fraud_indicator and fraud_evidence cannot both be empty.",
                success=False, done=False, reward=-0.05,
            )

        # Check if agent fell for a honeypot
        for hp in honeypots:
            if self._fuzzy_match_honeypot(indicator, evidence, hp):
                self._honeypots_triggered.append(hp.get("name", indicator))
                penalty = HONEYPOT_PENALTY
                self._scores["honeypot_penalty"] = self._scores.get("honeypot_penalty", 0) + penalty
                return self._make_observation(
                    f"HONEYPOT TRIGGERED: '{indicator}' matches planted decoy evidence. "
                    f"This was a trap — the evidence is fabricated. Penalty applied.\n"
                    f"Hint: {hp.get('hint', 'Look more carefully at the supporting evidence.')}",
                    success=False, done=False, reward=penalty,
                )

        # Check if this flag matches a real fraud indicator
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
            score = -0.01
            result_text = (
                f"Fraud flag '{indicator}' not matched to known indicators. "
                f"Fraud flags found so far: {len(self._fraud_flags_found)}/{len(gt_flags)}"
            )

        return self._make_observation(result_text, success=matched, done=False, reward=score)

    def _handle_request_info(self, action: ClaimsAction) -> ClaimsObservation:
        question = (action.info_question or "").strip()

        result_text = (
            f"Information request: '{question}'\n\n"
            "Refer to the policy document and supporting evidence provided. "
            "All available information has been included in the initial observation."
        )

        if question and not self._request_info_rewarded:
            score = 0.01
            self._request_info_rewarded = True
        else:
            score = 0.0

        return self._make_observation(result_text, success=True, done=False, reward=score)

    def _handle_issue_decision(self, action: ClaimsAction) -> ClaimsObservation:
        """Handle final decision — grades and ends the episode.

        Also computes:
        - Investigation order bonus (did agent follow logical workflow?)
        - Efficiency bonus (did agent finish quickly?)
        - Honeypot penalties (did agent fall for fake evidence?)
        """
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

        if agent_decision == correct_decision:
            decision_score += 0.6
        elif (agent_decision in ("approve", "partial_approve") and
              correct_decision in ("approve", "partial_approve")):
            decision_score += 0.3
        # deny vs approve = 0

        if correct_amount > 0:
            error_ratio = abs(agent_amount - correct_amount) / correct_amount
            amount_accuracy = max(0.0, 1.0 - error_ratio)
            decision_score += 0.3 * amount_accuracy
        elif correct_amount == 0:
            decision_score += 0.3 if agent_amount == 0 else 0.0

        if agent_reasoning and len(agent_reasoning) > 20:
            decision_score += 0.1

        decision_score = min(decision_score, 1.0)
        score = weight * decision_score
        self._scores["decision"] = score

        # --- Investigation order bonus ---
        order_bonus = self._compute_order_bonus()
        if order_bonus > 0:
            self._scores["order_bonus"] = order_bonus

        # --- Efficiency bonus ---
        eff_bonus = self._compute_efficiency_bonus()
        if eff_bonus > 0:
            self._scores["efficiency_bonus"] = eff_bonus

        # --- Honeypot penalties (already tracked, just include in summary) ---

        total_score = self._clamp_score(sum(self._scores.values()))
        self._state.current_score = total_score

        result_text = (
            f"DECISION ISSUED: {agent_decision.upper()}\n"
            f"Amount: ${agent_amount:,.2f}\n"
            f"Reasoning: {agent_reasoning}\n\n"
            f"--- GRADING ---\n"
            f"Correct decision: {correct_decision.upper()}\n"
            f"Correct amount: ${correct_amount:,.2f}\n"
            f"Decision score: {decision_score*100:.1f}%\n"
        )

        if order_bonus > 0:
            result_text += f"Investigation order bonus: +{order_bonus:.3f}\n"
        if eff_bonus > 0:
            result_text += f"Efficiency bonus: +{eff_bonus:.3f} (used {self._state.step_count}/{self._max_steps} steps)\n"
        if self._honeypots_triggered:
            result_text += f"Honeypot penalties: {len(self._honeypots_triggered)} trap(s) triggered\n"

        result_text += f"\n--- FINAL SCORE BREAKDOWN ---\n"
        for category, s in sorted(self._scores.items()):
            w = self._task["scoring_weights"].get(category, 0)
            if w > 0:
                result_text += f"  {category}: {s:.3f} / {w:.3f}\n"
            else:
                result_text += f"  {category}: {s:+.3f} (bonus/penalty)\n"
        result_text += f"\nTOTAL SCORE: {total_score:.3f} / 1.000"

        return self._make_observation(
            result_text, success=(agent_decision == correct_decision),
            done=True, reward=score,
        )

    # --- Bonus/penalty computations ---

    def _compute_order_bonus(self) -> float:
        """Award bonus if agent followed the ideal investigation order.

        Measures how well the agent's action sequence matches the
        ideal workflow: eligibility -> coverage -> exclusion -> payout -> fraud -> decision.
        Uses longest common subsequence ratio.
        """
        # Extract unique action types in order (skip duplicates)
        seen = set()
        agent_order = []
        for a in self._actions_taken:
            if a not in seen and a in IDEAL_ORDER:
                seen.add(a)
                agent_order.append(a)

        if len(agent_order) < 3:
            return 0.0

        # Compute LCS length between agent_order and IDEAL_ORDER
        ideal = [a for a in IDEAL_ORDER if a in seen]
        lcs_len = self._lcs_length(agent_order, ideal)
        ratio = lcs_len / len(ideal) if ideal else 0

        if ratio >= 0.8:
            return ORDER_BONUS
        return 0.0

    def _compute_efficiency_bonus(self) -> float:
        """Award bonus if agent completed the task efficiently (fewer steps)."""
        if self._state.step_count <= 0 or self._max_steps <= 0:
            return 0.0

        usage_ratio = self._state.step_count / self._max_steps
        if usage_ratio <= EFFICIENCY_BONUS_THRESHOLD:
            return EFFICIENCY_BONUS
        return 0.0

    @staticmethod
    def _lcs_length(a: List[str], b: List[str]) -> int:
        """Compute length of longest common subsequence."""
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if a[i - 1] == b[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
        return dp[m][n]

    # --- Helpers ---

    @staticmethod
    def _clamp_score(value: float) -> float:
        """Clamp to strictly between 0 and 1 (validator rejects exact 0.0 or 1.0)."""
        if not math.isfinite(value):
            return 0.001
        return min(0.999, max(0.001, value))

    def _make_observation(
        self, result: str, success: bool, done: bool, reward: float
    ) -> ClaimsObservation:
        total_score = sum(self._scores.values())
        total_score = self._clamp_score(total_score)
        reward = self._clamp_score(reward)
        self._state.current_score = total_score

        return ClaimsObservation(
            task_id=self._task["task_id"] if self._task else (self._state.task_id or "uninitialized"),
            task_difficulty=(
                self._task["difficulty"] if self._task else (self._state.task_difficulty or "unknown")
            ),
            policy_document=None,
            claim_submission=None,
            supporting_evidence=None,
            action_result=result,
            action_success=success,
            score_breakdown={k: self._clamp_score(v) for k, v in self._scores.items()},
            current_score=total_score,
            steps_taken=self._state.step_count,
            max_steps=self._max_steps,
            done=done,
            reward=reward,
        )

    def _fuzzy_match_item(self, query: str, items: Dict[str, Any]) -> Optional[str]:
        query_lower = query.lower().strip()
        for key in items:
            if key in query_lower or query_lower in key:
                return key
        for key in items:
            key_words = set(key.replace("_", " ").split())
            query_words = set(query_lower.replace("_", " ").split())
            if key_words & query_words:
                return key
        return None

    def _fuzzy_match_fraud(
        self, indicator: str, evidence: str, gt_flag: Dict[str, Any]
    ) -> bool:
        ind_lower = indicator.lower().strip()
        ev_lower = evidence.lower().strip()
        gt_ind = gt_flag["indicator"].lower()

        if not ind_lower and not ev_lower:
            return False

        if ind_lower and (gt_ind in ind_lower or ind_lower in gt_ind):
            return True

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

    def _fuzzy_match_honeypot(
        self, indicator: str, evidence: str, honeypot: Dict[str, Any]
    ) -> bool:
        """Check if agent's fraud flag matches a honeypot trap."""
        combined = (indicator + " " + evidence).lower()
        triggers = honeypot.get("triggers", [])
        for trigger in triggers:
            if trigger.lower() in combined:
                return True
        return False
