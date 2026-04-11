"""
Data models for the Insurance Claims Adjudication Environment.

The agent processes insurance claims by reading policy documents, verifying
eligibility, checking coverage, calculating payouts, detecting fraud, and
issuing decisions. All actions and observations are strongly typed.
"""

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class ClaimsAction(Action):
    """Action the agent can take in the claims environment.

    The agent must specify an action_type and provide relevant parameters.
    Actions follow the real-world claims adjudication workflow.
    """

    action_type: Literal[
        "check_eligibility",
        "check_coverage",
        "check_exclusion",
        "calculate_payout",
        "flag_fraud",
        "request_info",
        "issue_decision",
    ] = Field(..., description="Type of action to perform")

    # For check_eligibility
    policy_id: Optional[str] = Field(
        default=None, description="Policy ID to verify eligibility for"
    )
    incident_date: Optional[str] = Field(
        default=None, description="Date of incident (YYYY-MM-DD)"
    )

    # For check_coverage / check_exclusion
    policy_section: Optional[str] = Field(
        default=None, description="Policy section to check (e.g., 'collision', 'comprehensive')"
    )
    claim_item: Optional[str] = Field(
        default=None, description="Specific claim item to check coverage for"
    )

    # For calculate_payout
    claimed_amount: Optional[float] = Field(
        default=None, description="Amount being claimed"
    )
    deductible: Optional[float] = Field(
        default=None, description="Deductible amount to apply"
    )
    coverage_limit: Optional[float] = Field(
        default=None, description="Maximum coverage limit"
    )
    coverage_rate: Optional[float] = Field(
        default=None, description="Coverage rate (0.0-1.0)"
    )

    # For flag_fraud
    fraud_indicator: Optional[str] = Field(
        default=None, description="Type of fraud indicator detected"
    )
    fraud_evidence: Optional[str] = Field(
        default=None, description="Evidence supporting the fraud flag"
    )

    # For request_info
    info_question: Optional[str] = Field(
        default=None, description="Question to ask for additional information"
    )

    # For issue_decision
    decision: Optional[Literal["approve", "deny", "partial_approve"]] = Field(
        default=None, description="Claim decision"
    )
    decision_amount: Optional[float] = Field(
        default=None, description="Approved payout amount"
    )
    decision_reasoning: Optional[str] = Field(
        default=None, description="Reasoning for the decision"
    )


class ClaimsObservation(Observation):
    """Observation returned by the claims environment after each action.

    Contains the result of the agent's action, the current claim context,
    and scoring information.
    """

    # Current task context (provided on reset)
    task_id: Optional[str] = Field(
        default=None, description="Current task identifier"
    )
    task_difficulty: Optional[str] = Field(
        default=None, description="Task difficulty: easy, medium, hard"
    )
    policy_document: Optional[str] = Field(
        default=None, description="Full text of the insurance policy"
    )
    claim_submission: Optional[str] = Field(
        default=None, description="Claim details submitted by the claimant"
    )
    supporting_evidence: Optional[List[str]] = Field(
        default=None, description="List of supporting documents/evidence"
    )

    # Action result
    action_result: Optional[str] = Field(
        default=None, description="Result of the last action taken"
    )
    action_success: bool = Field(
        default=True, description="Whether the last action succeeded"
    )

    # Running score breakdown
    score_breakdown: Optional[Dict[str, float]] = Field(
        default=None, description="Current score breakdown by category"
    )
    current_score: float = Field(
        default=0.01, description="Current cumulative score in range (0, 1)"
    )

    # Episode info
    steps_taken: int = Field(default=0, description="Number of steps taken so far")
    max_steps: int = Field(default=20, description="Maximum steps allowed")


class ClaimsState(State):
    """Extended state for the claims environment."""

    task_id: str = Field(default="", description="Current task ID")
    task_difficulty: str = Field(default="", description="Current task difficulty")
    actions_taken: List[str] = Field(
        default_factory=list, description="History of action types taken"
    )
    current_score: float = Field(default=0.01, description="Current score")
    eligibility_checked: bool = Field(default=False)
    coverage_checked: bool = Field(default=False)
    payout_calculated: bool = Field(default=False)
    decision_issued: bool = Field(default=False)
    fraud_flags: List[str] = Field(default_factory=list)
