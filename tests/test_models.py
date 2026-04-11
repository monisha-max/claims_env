"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from models import ClaimsAction, ClaimsObservation, ClaimsState


class TestClaimsAction:
    """Action model validation."""

    def test_valid_action_check_eligibility(self):
        a = ClaimsAction(action_type="check_eligibility", policy_id="POL-123", incident_date="2024-03-15")
        assert a.action_type == "check_eligibility"
        assert a.policy_id == "POL-123"

    def test_valid_action_check_coverage(self):
        a = ClaimsAction(action_type="check_coverage", policy_section="collision", claim_item="bumper")
        assert a.action_type == "check_coverage"

    def test_valid_action_calculate_payout(self):
        a = ClaimsAction(action_type="calculate_payout", claimed_amount=8500, deductible=500,
                         coverage_limit=25000, coverage_rate=0.80)
        assert a.claimed_amount == 8500

    def test_valid_action_flag_fraud(self):
        a = ClaimsAction(action_type="flag_fraud", fraud_indicator="timing", fraud_evidence="18 days")
        assert a.fraud_indicator == "timing"

    def test_valid_action_issue_decision(self):
        a = ClaimsAction(action_type="issue_decision", decision="approve",
                         decision_amount=6400, decision_reasoning="Covered")
        assert a.decision == "approve"

    def test_invalid_action_type_rejected(self):
        with pytest.raises(ValidationError):
            ClaimsAction(action_type="invalid_action")

    def test_invalid_decision_value_rejected(self):
        with pytest.raises(ValidationError):
            ClaimsAction(action_type="issue_decision", decision="maybe")

    def test_all_seven_action_types_accepted(self):
        types = [
            "check_eligibility", "check_coverage", "check_exclusion",
            "calculate_payout", "flag_fraud", "request_info", "issue_decision",
        ]
        for t in types:
            a = ClaimsAction(action_type=t)
            assert a.action_type == t

    def test_optional_fields_default_to_none(self):
        a = ClaimsAction(action_type="check_eligibility")
        assert a.policy_id is None
        assert a.incident_date is None
        assert a.fraud_indicator is None


class TestClaimsObservation:
    """Observation model validation."""

    def test_defaults(self):
        o = ClaimsObservation()
        assert o.done is False
        assert o.reward is None
        assert o.current_score == 0.01
        assert o.steps_taken == 0
        assert o.action_success is True

    def test_with_all_fields(self):
        o = ClaimsObservation(
            task_id="easy_auto_collision",
            task_difficulty="easy",
            policy_document="test policy",
            claim_submission="test claim",
            supporting_evidence=["ev1", "ev2"],
            action_result="result",
            current_score=0.5,
            done=True,
            reward=0.1,
        )
        assert o.task_id == "easy_auto_collision"
        assert o.done is True
        assert len(o.supporting_evidence) == 2


class TestClaimsState:
    """State model validation."""

    def test_defaults(self):
        s = ClaimsState()
        assert s.step_count == 0
        assert s.task_id == ""
        assert s.eligibility_checked is False
        assert s.fraud_flags == []

    def test_custom_values(self):
        s = ClaimsState(
            episode_id="ep-1", step_count=5, task_id="test",
            current_score=0.5, eligibility_checked=True,
            fraud_flags=["timing"],
        )
        assert s.step_count == 5
        assert s.fraud_flags == ["timing"]
