"""Tests for the ClaimsEnvironment core logic."""

import pytest

from models import ClaimsAction
from server.claims_env_environment import ClaimsEnvironment


ALL_FIXED_TASKS = [
    "easy_auto_collision", "easy_travel_cancellation",
    "medium_medical_exclusions", "medium_pet_surgery",
    "medium_life_benefit", "medium_liability_injury",
    "hard_property_fraud", "hard_flood_exclusion", "hard_disability_claim",
]


class TestReset:
    """Tests for reset() behavior."""

    def test_reset_returns_observation_with_policy(self, env):
        obs = env.reset(task_id="easy_auto_collision")
        assert obs.policy_document is not None
        assert len(obs.policy_document) > 100

    def test_reset_returns_claim_submission(self, env):
        obs = env.reset(task_id="easy_auto_collision")
        assert obs.claim_submission is not None
        assert len(obs.claim_submission) > 100

    def test_reset_returns_supporting_evidence(self, env):
        obs = env.reset(task_id="easy_auto_collision")
        assert obs.supporting_evidence is not None
        assert len(obs.supporting_evidence) >= 1

    def test_reset_clears_state(self, env):
        env.reset(task_id="easy_auto_collision")
        env.step(ClaimsAction(action_type="check_eligibility"))
        assert env.state.step_count == 1

        obs = env.reset(task_id="easy_auto_collision")
        assert env.state.step_count == 0
        assert obs.current_score <= 0.01  # clamped above 0
        assert obs.done is False

    def test_reset_default_is_easy(self, env):
        obs = env.reset()
        assert obs.task_id == "easy_auto_collision"

    def test_reset_sets_correct_task_id(self, env):
        for task_id in ALL_FIXED_TASKS:
            obs = env.reset(task_id=task_id)
            assert obs.task_id == task_id

    def test_reset_invalid_task_raises(self, env):
        with pytest.raises(KeyError):
            env.reset(task_id="nonexistent_task")

    def test_reset_done_is_false(self, env):
        obs = env.reset(task_id="easy_auto_collision")
        assert obs.done is False

    def test_reset_reward_is_near_zero(self, env):
        obs = env.reset(task_id="easy_auto_collision")
        assert 0.0 < obs.reward <= 0.01  # clamped above 0


class TestStep:
    """Tests for step() behavior."""

    def test_step_increments_step_count(self, easy_env):
        easy_env.step(ClaimsAction(action_type="check_eligibility"))
        assert easy_env.state.step_count == 1
        easy_env.step(ClaimsAction(action_type="check_coverage"))
        assert easy_env.state.step_count == 2

    def test_step_returns_observation(self, easy_env):
        obs = easy_env.step(ClaimsAction(action_type="check_eligibility"))
        assert isinstance(obs.action_result, str)
        assert len(obs.action_result) > 0

    def test_step_after_decision_returns_done(self, easy_env):
        easy_env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="test"))
        obs = easy_env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.done is True
        assert obs.reward <= 0.01  # penalty clamped above 0

    def test_step_policy_not_sent_after_reset(self, easy_env):
        obs = easy_env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.policy_document is None  # only sent on reset

    def test_max_steps_ends_episode(self, env):
        env.reset(task_id="easy_auto_collision")
        # Exhaust all steps
        for _ in range(20):
            obs = env.step(ClaimsAction(action_type="request_info", info_question="test"))
            if obs.done:
                break
        assert obs.done is True


class TestState:
    """Tests for state property."""

    def test_state_has_episode_id(self, easy_env):
        assert easy_env.state.episode_id is not None
        assert len(easy_env.state.episode_id) > 0

    def test_state_tracks_task_id(self, easy_env):
        assert easy_env.state.task_id == "easy_auto_collision"

    def test_state_tracks_difficulty(self, easy_env):
        assert easy_env.state.task_difficulty == "easy"

    def test_state_tracks_actions(self, easy_env):
        easy_env.step(ClaimsAction(action_type="check_eligibility"))
        easy_env.step(ClaimsAction(action_type="check_coverage"))
        assert easy_env.state.actions_taken == ["check_eligibility", "check_coverage"]

    def test_state_tracks_flags(self, hard_env):
        hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="timing",
            fraud_evidence="Policy too new"))
        assert "timing" in hard_env.state.fraud_flags

    def test_state_unique_episode_ids(self, env):
        env.reset(task_id="easy_auto_collision")
        id1 = env.state.episode_id
        env.reset(task_id="easy_auto_collision")
        id2 = env.state.episode_id
        assert id1 != id2


class TestScoring:
    """Tests for the grading system."""

    def test_eligibility_gives_reward(self, easy_env):
        obs = easy_env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.reward > 0
        assert obs.current_score > 0

    def test_coverage_gives_reward(self, easy_env):
        obs = easy_env.step(ClaimsAction(action_type="check_coverage", policy_section="collision"))
        assert obs.reward > 0

    def test_exclusion_gives_reward(self, easy_env):
        obs = easy_env.step(ClaimsAction(action_type="check_exclusion"))
        assert obs.reward > 0

    def test_payout_accuracy_affects_score(self, easy_env):
        # Correct payout: 6400
        obs_correct = easy_env.step(ClaimsAction(
            action_type="calculate_payout", claimed_amount=8500,
            deductible=500, coverage_limit=25000, coverage_rate=0.80))
        score_correct = obs_correct.current_score

        # Reset and try wrong payout
        easy_env_2 = ClaimsEnvironment()
        easy_env_2.reset(task_id="easy_auto_collision")
        obs_wrong = easy_env_2.step(ClaimsAction(
            action_type="calculate_payout", claimed_amount=8500,
            deductible=0, coverage_limit=25000, coverage_rate=0.50))
        score_wrong = obs_wrong.current_score

        assert score_correct > score_wrong

    def test_decision_correct_gives_high_reward(self, easy_env):
        obs = easy_env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="Collision covered"))
        assert obs.reward > 0.1

    def test_decision_wrong_gives_low_reward(self, easy_env):
        obs = easy_env.step(ClaimsAction(
            action_type="issue_decision", decision="deny",
            decision_amount=0, decision_reasoning="Denied"))
        assert obs.reward < 0.1

    def test_score_breakdown_populated(self, easy_env):
        easy_env.step(ClaimsAction(action_type="check_eligibility"))
        obs = easy_env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="test"))
        assert obs.score_breakdown is not None
        assert "eligibility" in obs.score_breakdown
        assert "decision" in obs.score_breakdown

    def test_all_scores_strictly_between_0_and_1(self, env):
        for task_id in ALL_FIXED_TASKS:
            env.reset(task_id=task_id)
            env.step(ClaimsAction(action_type="check_eligibility"))
            obs = env.step(ClaimsAction(
                action_type="issue_decision", decision="approve",
                decision_amount=0, decision_reasoning="test"))
            assert 0.0 < obs.current_score < 1.0, f"{task_id}: score {obs.current_score}"

    def test_cumulative_score_increases(self, easy_env):
        scores = []
        for action_type in ["check_eligibility", "check_coverage", "check_exclusion"]:
            obs = easy_env.step(ClaimsAction(action_type=action_type))
            scores.append(obs.current_score)
        # Score should be non-decreasing
        assert scores[0] <= scores[1] <= scores[2]


class TestFraudDetection:
    """Tests for fraud flagging in hard tasks."""

    def test_correct_fraud_flag_rewarded(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="timing",
            fraud_evidence="Only 18 days between inception and claim"))
        assert obs.reward > 0

    def test_incorrect_fraud_flag_low_reward(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="completely_made_up",
            fraud_evidence="No real evidence"))
        assert obs.reward <= 0.01  # penalty clamped above 0

    def test_empty_fraud_flag_rejected(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="", fraud_evidence=""))
        assert obs.action_success is False
        assert obs.reward <= 0.01  # penalty clamped above 0

    def test_duplicate_fraud_flag_no_double_reward(self, hard_env):
        obs1 = hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="timing",
            fraud_evidence="Policy too new"))
        r1 = obs1.reward

        obs2 = hard_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="timing",
            fraud_evidence="Policy too new again"))
        r2 = obs2.reward

        assert r1 > 0.01  # real reward
        assert r2 <= 0.01  # no double reward (clamped)

    def test_false_fraud_on_clean_claim_penalized(self, easy_env):
        obs = easy_env.step(ClaimsAction(
            action_type="flag_fraud", fraud_indicator="timing",
            fraud_evidence="Suspicious"))
        assert obs.reward <= 0.01  # penalty clamped above 0

    def test_deny_fraud_claim_correct(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="issue_decision", decision="deny",
            decision_amount=0, decision_reasoning="Fraud detected"))
        assert obs.reward > 0.1

    def test_approve_fraud_claim_low_score(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=50000, decision_reasoning="Approved"))
        assert obs.reward < 0.05


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_request_info_capped_at_one_reward(self, easy_env):
        obs1 = easy_env.step(ClaimsAction(
            action_type="request_info", info_question="What coverage?"))
        obs2 = easy_env.step(ClaimsAction(
            action_type="request_info", info_question="What deductible?"))
        assert obs1.reward > 0.005  # first request gets real reward
        assert obs2.reward <= 0.005  # second gets only clamp minimum

    def test_multiple_coverage_checks_diminishing(self, easy_env):
        obs1 = easy_env.step(ClaimsAction(action_type="check_coverage"))
        r1 = obs1.reward
        obs2 = easy_env.step(ClaimsAction(action_type="check_coverage"))
        r2 = obs2.reward
        assert r1 > r2  # first check worth more

    def test_step_without_reset_still_works(self):
        env = ClaimsEnvironment()
        env.reset(task_id="easy_auto_collision")
        obs = env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.action_result is not None

    def test_rapid_reset_clears_everything(self, env):
        env.reset(task_id="easy_auto_collision")
        env.step(ClaimsAction(action_type="check_eligibility"))
        env.step(ClaimsAction(action_type="flag_fraud",
                              fraud_indicator="test", fraud_evidence="test"))
        env.reset(task_id="hard_property_fraud")
        assert env.state.step_count == 0
        assert env.state.current_score <= 0.01
        assert env.state.fraud_flags == []
        assert env.state.eligibility_checked is False

    def test_score_never_exactly_zero(self, env):
        """Validator requires scores strictly > 0."""
        env.reset(task_id="easy_auto_collision")
        obs = env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.current_score > 0.0

    def test_score_never_exactly_one(self, env):
        """Validator requires scores strictly < 1."""
        env.reset(task_id="easy_auto_collision")
        env.step(ClaimsAction(action_type="check_eligibility"))
        env.step(ClaimsAction(action_type="check_coverage"))
        env.step(ClaimsAction(action_type="check_exclusion"))
        env.step(ClaimsAction(action_type="calculate_payout",
                              claimed_amount=8500, deductible=500,
                              coverage_limit=25000, coverage_rate=0.80))
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="test"))
        assert obs.current_score < 1.0

    def test_score_clamped_on_no_actions(self, env):
        """Even with minimal actions, score should be > 0."""
        env.reset(task_id="hard_property_fraud")
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="deny",
            decision_amount=0, decision_reasoning="deny"))
        assert obs.current_score > 0.0
        assert obs.current_score < 1.0

    def test_efficiency_bonus_awarded(self, env):
        """Agent that finishes in few steps gets efficiency bonus."""
        env.reset(task_id="easy_auto_collision")
        env.step(ClaimsAction(action_type="check_eligibility"))
        env.step(ClaimsAction(action_type="check_coverage"))
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="Quick and correct"))
        assert "efficiency_bonus" in obs.score_breakdown

    def test_order_bonus_for_correct_workflow(self, env):
        """Agent that follows ideal order gets order bonus."""
        env.reset(task_id="easy_auto_collision")
        env.step(ClaimsAction(action_type="check_eligibility"))
        env.step(ClaimsAction(action_type="check_coverage"))
        env.step(ClaimsAction(action_type="check_exclusion"))
        env.step(ClaimsAction(action_type="calculate_payout",
                              claimed_amount=8500, deductible=500,
                              coverage_limit=25000, coverage_rate=0.80))
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=6400, decision_reasoning="Complete workflow"))
        assert "order_bonus" in obs.score_breakdown

    def test_honeypot_penalty_on_hard_task(self, env):
        """Agent that flags honeypot evidence gets penalized."""
        env.reset(task_id="hard_property_fraud")
        obs = env.step(ClaimsAction(
            action_type="flag_fraud",
            fraud_indicator="weather damage",
            fraud_evidence="Storm caused the damage"))
        assert "HONEYPOT" in obs.action_result
        assert obs.action_success is False

    def test_no_honeypot_on_easy_task(self, env):
        """Easy tasks have no honeypots."""
        env.reset(task_id="easy_auto_collision")
        obs = env.step(ClaimsAction(
            action_type="flag_fraud",
            fraud_indicator="weather",
            fraud_evidence="Storm"))
        assert "HONEYPOT" not in obs.action_result

    def test_decision_amount_zero_on_denial(self, hard_env):
        obs = hard_env.step(ClaimsAction(
            action_type="issue_decision", decision="deny",
            decision_amount=0, decision_reasoning="Fraud"))
        # Should get credit for correct amount (0)
        assert obs.current_score > 0
