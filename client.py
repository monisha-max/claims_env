"""Insurance Claims Adjudication Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import ClaimsAction, ClaimsObservation, ClaimsState


class ClaimsEnv(EnvClient[ClaimsAction, ClaimsObservation, ClaimsState]):
    """
    Client for the Insurance Claims Adjudication Environment.

    Connects via WebSocket to the environment server. Each client gets
    its own isolated claims adjudication session.

    Example:
        >>> from claims_env import ClaimsEnv, ClaimsAction
        >>>
        >>> with ClaimsEnv(base_url="http://localhost:8000").sync() as env:
        ...     result = env.reset(task_id="easy_auto_collision")
        ...     print(result.observation.policy_document)
        ...
        ...     result = env.step(ClaimsAction(
        ...         action_type="check_eligibility",
        ...         policy_id="POL-2024-78432",
        ...         incident_date="2024-03-15",
        ...     ))
        ...     print(result.observation.action_result)
    """

    def _step_payload(self, action: ClaimsAction) -> Dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[ClaimsObservation]:
        obs_data = payload.get("observation", {})
        observation = ClaimsObservation(
            task_id=obs_data.get("task_id"),
            task_difficulty=obs_data.get("task_difficulty"),
            policy_document=obs_data.get("policy_document"),
            claim_submission=obs_data.get("claim_submission"),
            supporting_evidence=obs_data.get("supporting_evidence"),
            action_result=obs_data.get("action_result"),
            action_success=obs_data.get("action_success", True),
            score_breakdown=obs_data.get("score_breakdown"),
            current_score=obs_data.get("current_score", 0.0),
            steps_taken=obs_data.get("steps_taken", 0),
            max_steps=obs_data.get("max_steps", 20),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> ClaimsState:
        return ClaimsState(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
            task_id=payload.get("task_id", ""),
            task_difficulty=payload.get("task_difficulty", ""),
            actions_taken=payload.get("actions_taken", []),
            current_score=payload.get("current_score", 0.0),
            eligibility_checked=payload.get("eligibility_checked", False),
            coverage_checked=payload.get("coverage_checked", False),
            payout_calculated=payload.get("payout_calculated", False),
            decision_issued=payload.get("decision_issued", False),
            fraud_flags=payload.get("fraud_flags", []),
        )
