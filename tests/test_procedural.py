"""Tests for procedural scenario generation."""

import pytest

from models import ClaimsAction
from server.claims_env_environment import ClaimsEnvironment
from server.generator.scenario_generator import ScenarioGenerator


class TestScenarioGenerator:
    """Tests for the ScenarioGenerator."""

    def test_generates_valid_scenario(self):
        gen = ScenarioGenerator(seed=42, difficulty="easy")
        scenario = gen.generate()
        assert "policy_document" in scenario
        assert "claim_submission" in scenario
        assert "supporting_evidence" in scenario
        assert "ground_truth" in scenario

    def test_ground_truth_has_required_fields(self):
        gen = ScenarioGenerator(seed=42, difficulty="medium")
        scenario = gen.generate()
        gt = scenario["ground_truth"]
        assert "eligibility" in gt
        assert "coverage" in gt
        assert "exclusions" in gt
        assert "payout" in gt
        assert "correct_decision" in gt
        assert "correct_decision_amount" in gt

    @pytest.mark.parametrize("insurance_type", ["auto", "medical", "home", "travel"])
    def test_all_insurance_types(self, insurance_type):
        gen = ScenarioGenerator(seed=42, difficulty="medium", insurance_type=insurance_type)
        scenario = gen.generate()
        assert insurance_type in scenario["task_id"]
        assert len(scenario["policy_document"]) > 200
        assert len(scenario["_claim_data"]["line_items"]) >= 2

    @pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
    def test_all_difficulties(self, difficulty):
        gen = ScenarioGenerator(seed=42, difficulty=difficulty)
        scenario = gen.generate()
        assert scenario["difficulty"] == difficulty

    def test_hard_has_fraud_flags(self):
        gen = ScenarioGenerator(seed=42, difficulty="hard")
        scenario = gen.generate()
        assert len(scenario["ground_truth"]["fraud_flags"]) >= 3

    def test_easy_has_no_fraud(self):
        gen = ScenarioGenerator(seed=42, difficulty="easy")
        scenario = gen.generate()
        assert len(scenario["ground_truth"]["fraud_flags"]) == 0

    def test_hard_decision_is_deny(self):
        gen = ScenarioGenerator(seed=42, difficulty="hard")
        scenario = gen.generate()
        assert scenario["ground_truth"]["correct_decision"] == "deny"
        assert scenario["ground_truth"]["correct_decision_amount"] == 0

    def test_payout_is_non_negative(self):
        for seed in range(50):
            for diff in ["easy", "medium", "hard"]:
                gen = ScenarioGenerator(seed=seed, difficulty=diff)
                scenario = gen.generate()
                payout = scenario["ground_truth"]["payout"]["correct_payout"]
                assert payout >= 0, f"seed={seed} diff={diff} payout={payout}"


class TestReproducibility:
    """Same seed must produce identical scenarios."""

    def test_same_seed_same_policy(self):
        s1 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        s2 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        assert s1["policy_document"] == s2["policy_document"]

    def test_same_seed_same_claim(self):
        s1 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        s2 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        assert s1["claim_submission"] == s2["claim_submission"]

    def test_same_seed_same_ground_truth(self):
        s1 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        s2 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        assert s1["ground_truth"]["payout"]["correct_payout"] == \
               s2["ground_truth"]["payout"]["correct_payout"]

    def test_different_seed_different_scenario(self):
        s1 = ScenarioGenerator(seed=42, difficulty="medium").generate()
        s2 = ScenarioGenerator(seed=43, difficulty="medium").generate()
        assert s1["policy_document"] != s2["policy_document"]

    @pytest.mark.parametrize("seed", [0, 1, 100, 999, 12345])
    def test_reproducibility_across_seeds(self, seed):
        s1 = ScenarioGenerator(seed=seed, difficulty="easy").generate()
        s2 = ScenarioGenerator(seed=seed, difficulty="easy").generate()
        assert s1["ground_truth"] == s2["ground_truth"]


class TestProceduralIntegration:
    """Tests for procedural generation via environment reset()."""

    def test_reset_with_difficulty(self):
        env = ClaimsEnvironment()
        obs = env.reset(difficulty="easy", seed=42)
        assert obs.task_id.startswith("generated_")
        assert obs.policy_document is not None

    def test_reset_with_specific_type(self):
        env = ClaimsEnvironment()
        obs = env.reset(difficulty="medium", insurance_type="medical", seed=42)
        assert "medical" in obs.task_id

    def test_procedural_step_works(self):
        env = ClaimsEnvironment()
        env.reset(difficulty="easy", seed=42)
        obs = env.step(ClaimsAction(action_type="check_eligibility"))
        assert obs.reward > 0
        assert obs.current_score > 0

    def test_procedural_full_episode(self):
        env = ClaimsEnvironment()
        env.reset(difficulty="easy", seed=42)
        env.step(ClaimsAction(action_type="check_eligibility"))
        env.step(ClaimsAction(action_type="check_coverage"))
        env.step(ClaimsAction(action_type="check_exclusion"))
        obs = env.step(ClaimsAction(
            action_type="issue_decision", decision="approve",
            decision_amount=5000, decision_reasoning="test"))
        assert obs.done is True
        assert 0.0 <= obs.current_score <= 1.0

    def test_procedural_and_fixed_coexist(self):
        env = ClaimsEnvironment()

        # Procedural
        obs1 = env.reset(difficulty="easy", seed=42)
        assert obs1.task_id.startswith("generated_")

        # Fixed
        obs2 = env.reset(task_id="easy_auto_collision")
        assert obs2.task_id == "easy_auto_collision"

        # Procedural again
        obs3 = env.reset(difficulty="hard", seed=99)
        assert obs3.task_id.startswith("generated_")

    def test_100_seeds_no_crashes(self):
        env = ClaimsEnvironment()
        for seed in range(100):
            obs = env.reset(difficulty="medium", seed=seed)
            assert obs.policy_document is not None
            obs = env.step(ClaimsAction(action_type="check_eligibility"))
            assert obs.current_score >= 0

    def test_variety_across_seeds(self):
        env = ClaimsEnvironment()
        task_ids = set()
        for seed in range(50):
            obs = env.reset(difficulty="medium", seed=seed)
            task_ids.add(obs.task_id)
        # Should have many unique scenarios
        assert len(task_ids) == 50
