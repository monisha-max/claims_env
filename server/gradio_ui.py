"""
Interactive Gradio web UI for the Insurance Claims Adjudication Environment.

Judges and users can play as a claims adjuster directly in their browser:
- Read the policy and claim
- Take actions (check eligibility, coverage, exclusions, calculate payout, flag fraud)
- Issue a decision and see their score

Accessible at /web when ENABLE_WEB_INTERFACE=true.
"""

try:
    import gradio as gr
except ImportError:
    gr = None

from typing import List, Tuple

def build_gradio_app(env_factory):
    """Build a Gradio interface for the claims environment."""
    if gr is None:
        return None

    def reset_env(task_id):
        env = env_factory()
        obs = env.reset(task_id=task_id)
        context = (
            f"**Policy Document:**\n\n{obs.policy_document}\n\n"
            f"---\n\n**Claim Submission:**\n\n{obs.claim_submission}\n\n"
            f"---\n\n**Supporting Evidence:**\n\n"
        )
        for i, ev in enumerate(obs.supporting_evidence or [], 1):
            context += f"{i}. {ev}\n\n"

        status = f"Task: {obs.task_id} | Difficulty: {obs.task_difficulty} | Max steps: {obs.max_steps}"
        return env, context, status, "", "0.001", "0 / " + str(obs.max_steps), []

    def take_action(env, action_type, policy_section, claim_item,
                    claimed_amount, deductible, coverage_limit, coverage_rate,
                    fraud_indicator, fraud_evidence, decision, decision_amount,
                    decision_reasoning, history):
        if env is None:
            return env, "Reset the environment first.", "", "", history

        from models import ClaimsAction

        kwargs = {"action_type": action_type}
        if action_type == "check_eligibility":
            kwargs["policy_id"] = "from_ui"
            kwargs["incident_date"] = "from_ui"
        elif action_type in ("check_coverage", "check_exclusion"):
            kwargs["policy_section"] = policy_section
            kwargs["claim_item"] = claim_item
        elif action_type == "calculate_payout":
            kwargs["claimed_amount"] = float(claimed_amount) if claimed_amount else 0
            kwargs["deductible"] = float(deductible) if deductible else 0
            kwargs["coverage_limit"] = float(coverage_limit) if coverage_limit else 0
            kwargs["coverage_rate"] = float(coverage_rate) if coverage_rate else 0
        elif action_type == "flag_fraud":
            kwargs["fraud_indicator"] = fraud_indicator
            kwargs["fraud_evidence"] = fraud_evidence
        elif action_type == "issue_decision":
            kwargs["decision"] = decision
            kwargs["decision_amount"] = float(decision_amount) if decision_amount else 0
            kwargs["decision_reasoning"] = decision_reasoning

        action = ClaimsAction(**kwargs)
        obs = env.step(action)

        result = obs.action_result or ""
        score = f"{obs.current_score:.3f}"
        steps = f"{obs.steps_taken} / {obs.max_steps}"

        history = history or []
        history.append(f"**Step {obs.steps_taken}** [{action_type}]: reward={obs.reward:.3f}, score={obs.current_score:.3f}")
        if obs.done:
            history.append(f"\n**EPISODE COMPLETE** - Final score: {obs.current_score:.3f}")
            if obs.score_breakdown:
                for k, v in obs.score_breakdown.items():
                    history.append(f"  {k}: {v:.3f}")

        history_text = "\n".join(history)
        return env, result, score, steps, history

    task_choices = [
        "easy_auto_collision", "easy_travel_cancellation",
        "medium_medical_exclusions", "medium_pet_surgery",
        "medium_life_benefit", "medium_liability_injury",
        "hard_property_fraud", "hard_flood_exclusion", "hard_disability_claim",
    ]

    with gr.Blocks(title="Insurance Claims Adjudication", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Insurance Claims Adjudication Environment")
        gr.Markdown("Play as a claims adjuster. Read the policy and claim, then take actions to adjudicate.")

        env_state = gr.State(None)
        history_state = gr.State([])

        with gr.Row():
            task_dropdown = gr.Dropdown(choices=task_choices, value="easy_auto_collision", label="Select Task")
            reset_btn = gr.Button("Reset Environment", variant="primary")

        with gr.Row():
            with gr.Column(scale=2):
                context_box = gr.Markdown(label="Policy & Claim", value="Click 'Reset Environment' to start.")
            with gr.Column(scale=1):
                status_box = gr.Textbox(label="Status", interactive=False)
                score_box = gr.Textbox(label="Current Score", interactive=False, value="0.001")
                steps_box = gr.Textbox(label="Steps", interactive=False)

        gr.Markdown("## Take an Action")

        with gr.Row():
            action_type = gr.Dropdown(
                choices=["check_eligibility", "check_coverage", "check_exclusion",
                         "calculate_payout", "flag_fraud", "request_info", "issue_decision"],
                value="check_eligibility", label="Action Type"
            )
            action_btn = gr.Button("Execute Action", variant="secondary")

        with gr.Row():
            policy_section = gr.Textbox(label="Policy Section", placeholder="e.g., collision, inpatient")
            claim_item = gr.Textbox(label="Claim Item", placeholder="e.g., bumper, surgery")

        with gr.Row():
            claimed_amount = gr.Number(label="Claimed Amount", value=0)
            deductible = gr.Number(label="Deductible", value=0)
            coverage_limit = gr.Number(label="Coverage Limit", value=0)
            coverage_rate = gr.Number(label="Coverage Rate (0-1)", value=0)

        with gr.Row():
            fraud_indicator = gr.Textbox(label="Fraud Indicator", placeholder="e.g., timing, inflated_values")
            fraud_evidence = gr.Textbox(label="Fraud Evidence", placeholder="Describe the evidence")

        with gr.Row():
            decision = gr.Dropdown(choices=["approve", "deny", "partial_approve"], value="approve", label="Decision")
            decision_amount = gr.Number(label="Decision Amount", value=0)
            decision_reasoning = gr.Textbox(label="Decision Reasoning", placeholder="Explain your decision")

        result_box = gr.Markdown(label="Action Result", value="")
        history_box = gr.Markdown(label="Action History", value="")

        reset_btn.click(
            fn=reset_env,
            inputs=[task_dropdown],
            outputs=[env_state, context_box, status_box, result_box, score_box, steps_box, history_state],
        )

        action_btn.click(
            fn=take_action,
            inputs=[env_state, action_type, policy_section, claim_item,
                    claimed_amount, deductible, coverage_limit, coverage_rate,
                    fraud_indicator, fraud_evidence, decision, decision_amount,
                    decision_reasoning, history_state],
            outputs=[env_state, result_box, score_box, steps_box, history_state],
        )

    return demo
