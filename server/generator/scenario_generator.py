"""
Procedural scenario generator for insurance claims.

Generates structured policy data → claim data → ground truth,
then renders everything as human-readable text. Every reset()
with a different seed produces a unique, valid scenario.
"""

import random
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from . import pools


class ScenarioGenerator:
    """Generates complete insurance claim scenarios with ground truth.

    Usage:
        gen = ScenarioGenerator(seed=42, difficulty="medium")
        scenario = gen.generate()
        # scenario has: policy_document, claim_submission, supporting_evidence,
        #               ground_truth, scoring_weights, task_id, difficulty, max_steps
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        difficulty: str = "medium",
        insurance_type: Optional[str] = None,
    ):
        self.rng = random.Random(seed)
        self.difficulty = difficulty
        self.insurance_type = insurance_type or self.rng.choice(pools.INSURANCE_TYPES)
        self.seed = seed

    def generate(self) -> Dict[str, Any]:
        """Generate a complete scenario with policy, claim, evidence, and ground truth."""
        policy_data = self._generate_policy()
        claim_data = self._generate_claim(policy_data)
        ground_truth = self._compute_ground_truth(policy_data, claim_data)

        policy_text = self._render_policy(policy_data)
        claim_text = self._render_claim(claim_data, policy_data)
        evidence = self._render_evidence(claim_data, policy_data)

        # Scoring weights vary by difficulty
        scoring_weights = self._get_scoring_weights()

        max_steps = {"easy": 15, "medium": 20, "hard": 25}[self.difficulty]

        task_id = f"generated_{self.insurance_type}_{self.difficulty}_{self.seed or 'random'}"

        return {
            "task_id": task_id,
            "difficulty": self.difficulty,
            "max_steps": max_steps,
            "policy_document": policy_text,
            "claim_submission": claim_text,
            "supporting_evidence": evidence,
            "ground_truth": ground_truth,
            "scoring_weights": scoring_weights,
            # Store structured data for debugging
            "_policy_data": policy_data,
            "_claim_data": claim_data,
        }

    # ─── Policy Generation ───────────────────────────────────────────

    def _generate_policy(self) -> Dict[str, Any]:
        holder_first = self.rng.choice(pools.FIRST_NAMES)
        holder_last = self.rng.choice(pools.LAST_NAMES)

        # Random policy dates
        year = self.rng.choice([2023, 2024])
        month = self.rng.randint(1, 12)
        start = date(year, month, 1)
        end = start.replace(year=start.year + 1)

        policy = {
            "type": self.insurance_type,
            "id": f"POL-{year}-{self.rng.randint(10000, 99999)}",
            "holder_first": holder_first,
            "holder_last": holder_last,
            "holder_name": f"{holder_first} {holder_last}",
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "premium_status": self.rng.choice(["paid", "paid", "paid", "current"]),
            "sections": {},
            "exclusions": [],
            "conditions": {},
        }

        if self.insurance_type == "auto":
            self._fill_auto_policy(policy)
        elif self.insurance_type == "medical":
            self._fill_medical_policy(policy)
        elif self.insurance_type == "home":
            self._fill_home_policy(policy)
        elif self.insurance_type == "travel":
            self._fill_travel_policy(policy)

        return policy

    def _fill_auto_policy(self, policy: Dict):
        # Pick 2-3 sections
        section_keys = self.rng.sample(list(pools.AUTO_SECTIONS.keys()),
                                        k=self.rng.randint(2, 3))
        for key in section_keys:
            tmpl = pools.AUTO_SECTIONS[key]
            policy["sections"][key] = {
                "description": tmpl["description"],
                "deductible": self._round_to(self.rng.randint(*tmpl["deductible_range"]), 50),
                "limit": self._round_to(self.rng.randint(*tmpl["limit_range"]), 1000),
                "rate": round(self.rng.uniform(*tmpl["rate_range"]), 2),
            }

        num_exclusions = {"easy": 2, "medium": 3, "hard": 4}[self.difficulty]
        policy["exclusions"] = self.rng.sample(pools.AUTO_EXCLUSIONS, k=num_exclusions)
        policy["conditions"] = {
            "deadline_days": self.rng.choice([14, 30, 60]),
            "police_threshold": self.rng.choice([1000, 2000, 2500]),
        }

    def _fill_medical_policy(self, policy: Dict):
        for key, tmpl in pools.MEDICAL_SECTIONS.items():
            section = {"description": tmpl["description"], "sub_items": {}}
            if "deductible_range" in tmpl:
                section["deductible"] = self._round_to(
                    self.rng.randint(*tmpl["deductible_range"]), 100)
            if "limit_range" in tmpl:
                section["limit"] = self._round_to(
                    self.rng.randint(*tmpl["limit_range"]), 5000)
            for sub_key, sub_tmpl in tmpl["sub_items"].items():
                sub = {"label": sub_tmpl["label"]}
                if "rate_range" in sub_tmpl:
                    sub["rate"] = round(self.rng.uniform(*sub_tmpl["rate_range"]), 2)
                if "copay_range" in sub_tmpl:
                    sub["copay"] = self._round_to(
                        self.rng.randint(*sub_tmpl["copay_range"]), 5)
                if "session_limit" in sub_tmpl:
                    sub["session_limit"] = self.rng.randint(*sub_tmpl["session_limit"])
                section["sub_items"][sub_key] = sub
            policy["sections"][key] = section

        num_exclusions = {"easy": 2, "medium": 4, "hard": 5}[self.difficulty]
        exclusions = self.rng.sample(pools.MEDICAL_EXCLUSIONS, k=num_exclusions)
        # Fill in waiting period for pre_existing if present
        for exc in exclusions:
            if exc["id"] == "pre_existing":
                exc["text"] = exc["text"].format(waiting_months=self.rng.choice([3, 6, 12]))
        policy["exclusions"] = exclusions
        policy["conditions"] = {
            "deadline_days": self.rng.choice([60, 90, 120]),
            "pre_auth_required": True,
        }

    def _fill_home_policy(self, policy: Dict):
        for key, tmpl in pools.HOME_SECTIONS.items():
            section = {"description": tmpl["description"]}
            if "deductible_range" in tmpl:
                section["deductible"] = self._round_to(
                    self.rng.randint(*tmpl["deductible_range"]), 250)
            if "limit_range" in tmpl:
                section["limit"] = self._round_to(
                    self.rng.randint(*tmpl["limit_range"]), 5000)
            if "rate_range" in tmpl:
                section["rate"] = round(self.rng.uniform(*tmpl["rate_range"]), 2)
            if "high_value_cap" in tmpl:
                section["high_value_cap"] = tmpl["high_value_cap"]
            policy["sections"][key] = section

        num_exclusions = {"easy": 2, "medium": 4, "hard": 5}[self.difficulty]
        exclusions = self.rng.sample(pools.HOME_EXCLUSIONS, k=num_exclusions)
        for exc in exclusions:
            if exc["id"] == "vacancy":
                exc["text"] = exc["text"].format(vacancy_days=self.rng.choice([30, 60, 90]))
        policy["exclusions"] = exclusions
        policy["conditions"] = {
            "deadline_days": self.rng.choice([14, 30]),
            "proof_of_loss_days": self.rng.choice([30, 60]),
            "receipt_threshold": self.rng.choice([250, 500]),
        }

    def _fill_travel_policy(self, policy: Dict):
        for key, tmpl in pools.TRAVEL_SECTIONS.items():
            section = {"description": tmpl["description"]}
            if "deductible_range" in tmpl:
                section["deductible"] = self._round_to(
                    self.rng.randint(*tmpl["deductible_range"]), 50)
            if "limit_range" in tmpl:
                section["limit"] = self._round_to(
                    self.rng.randint(*tmpl["limit_range"]), 500)
            if "rate_range" in tmpl:
                section["rate"] = round(self.rng.uniform(*tmpl["rate_range"]), 2)
            if "covered_reasons" in tmpl:
                section["covered_reasons"] = tmpl["covered_reasons"]
            if "per_item_cap" in tmpl:
                section["per_item_cap"] = tmpl["per_item_cap"]
            policy["sections"][key] = section

        num_exclusions = {"easy": 2, "medium": 3, "hard": 4}[self.difficulty]
        policy["exclusions"] = self.rng.sample(pools.TRAVEL_EXCLUSIONS, k=num_exclusions)
        policy["conditions"] = {
            "deadline_days": self.rng.choice([14, 30]),
        }

    # ─── Claim Generation ────────────────────────────────────────────

    def _generate_claim(self, policy: Dict) -> Dict[str, Any]:
        # Incident date within policy period
        start = date.fromisoformat(policy["period_start"])
        end = date.fromisoformat(policy["period_end"])

        if self.difficulty == "hard":
            # For hard/fraud: incident soon after policy start
            days_after = self.rng.randint(5, 30)
        else:
            days_after = self.rng.randint(30, min(300, (end - start).days - 30))

        incident_date = start + timedelta(days=days_after)
        filed_delay = self.rng.randint(1, 10)
        filed_date = incident_date + timedelta(days=filed_delay)

        claim = {
            "id": f"CLM-{incident_date.year}-{self.rng.randint(10000, 99999)}",
            "incident_date": incident_date.isoformat(),
            "filed_date": filed_date.isoformat(),
            "line_items": [],
            "scenario": "",
            "fraud_indicators": [],
            "total_claimed": 0,
        }

        if self.insurance_type == "auto":
            self._fill_auto_claim(claim, policy)
        elif self.insurance_type == "medical":
            self._fill_medical_claim(claim, policy)
        elif self.insurance_type == "home":
            self._fill_home_claim(claim, policy)
        elif self.insurance_type == "travel":
            self._fill_travel_claim(claim, policy)

        # Inject fraud for hard difficulty
        if self.difficulty == "hard":
            self._inject_fraud(claim, policy)

        claim["total_claimed"] = sum(i["claimed_amount"] for i in claim["line_items"])
        return claim

    def _fill_auto_claim(self, claim: Dict, policy: Dict):
        claim["scenario"] = self.rng.choice(pools.AUTO_SCENARIOS)
        # Pick 3-6 items
        num_items = {"easy": 3, "medium": 4, "hard": 6}[self.difficulty]
        items = self.rng.sample(pools.AUTO_CLAIM_ITEMS, k=min(num_items, len(pools.AUTO_CLAIM_ITEMS)))

        # Determine primary section
        primary_section = "collision" if "collision" in policy["sections"] else list(policy["sections"].keys())[0]

        for item_tmpl in items:
            amount = self._round_to(self.rng.randint(*item_tmpl["range"]), 50)
            claim["line_items"].append({
                "name": item_tmpl["name"],
                "label": item_tmpl["label"],
                "claimed_amount": amount,
                "actual_amount": amount,
                "section": primary_section,
                "has_receipt": self.rng.random() > 0.3,
            })

        # For medium/hard, add an item that might not be covered
        if self.difficulty in ("medium", "hard"):
            excluded_ids = [e["id"] for e in policy["exclusions"]]
            if "commercial_use" in excluded_ids:
                claim["line_items"].append({
                    "name": "delivery_damage",
                    "label": "Damage during food delivery",
                    "claimed_amount": self.rng.randint(1000, 3000),
                    "actual_amount": 0,
                    "section": "excluded_commercial_use",
                    "has_receipt": False,
                })

    def _fill_medical_claim(self, claim: Dict, policy: Dict):
        claim["scenario"] = self.rng.choice(pools.MEDICAL_SCENARIOS)
        num_items = {"easy": 4, "medium": 6, "hard": 8}[self.difficulty]
        items = self.rng.sample(pools.MEDICAL_CLAIM_ITEMS, k=min(num_items, len(pools.MEDICAL_CLAIM_ITEMS)))

        for item_tmpl in items:
            amount = self._round_to(self.rng.randint(*item_tmpl["range"]), 50)
            claim["line_items"].append({
                "name": item_tmpl["name"],
                "label": item_tmpl["label"],
                "claimed_amount": amount,
                "actual_amount": amount,
                "section": item_tmpl["section"],
                "has_receipt": True,
            })

    def _fill_home_claim(self, claim: Dict, policy: Dict):
        claim["scenario"] = self.rng.choice(pools.HOME_SCENARIOS)
        # Mix of dwelling and personal property items
        num_dwelling = self.rng.randint(2, 4)
        num_personal = self.rng.randint(2, 5)

        dwelling_items = self.rng.sample(pools.HOME_CLAIM_ITEMS_DWELLING, k=min(num_dwelling, len(pools.HOME_CLAIM_ITEMS_DWELLING)))
        personal_items = self.rng.sample(pools.HOME_CLAIM_ITEMS_PERSONAL, k=min(num_personal, len(pools.HOME_CLAIM_ITEMS_PERSONAL)))

        for item_tmpl in dwelling_items:
            amount = self._round_to(self.rng.randint(*item_tmpl["range"]), 100)
            claim["line_items"].append({
                "name": item_tmpl["name"],
                "label": item_tmpl["label"],
                "claimed_amount": amount,
                "actual_amount": amount,
                "section": "dwelling",
                "has_receipt": True,
            })

        high_value_cap = policy["sections"].get("personal_property", {}).get("high_value_cap", 2500)
        for item_tmpl in personal_items:
            amount = self._round_to(self.rng.randint(*item_tmpl["range"]), 50)
            is_high_value = item_tmpl.get("high_value", False)
            actual = min(amount, high_value_cap) if is_high_value else amount
            claim["line_items"].append({
                "name": item_tmpl["name"],
                "label": item_tmpl["label"],
                "claimed_amount": amount,
                "actual_amount": actual,
                "section": "personal_property",
                "has_receipt": self.rng.random() > 0.4,
                "is_high_value": is_high_value,
            })

    def _fill_travel_claim(self, claim: Dict, policy: Dict):
        claim["scenario"] = self.rng.choice(pools.TRAVEL_SCENARIOS)
        primary_section = self.rng.choice(list(policy["sections"].keys()))

        num_items = {"easy": 2, "medium": 3, "hard": 4}[self.difficulty]
        for i in range(num_items):
            if primary_section == "trip_cancellation":
                items = [
                    ("flight", "Non-refundable flight tickets", (200, 2000)),
                    ("hotel", "Non-refundable hotel booking", (300, 3000)),
                    ("tour", "Pre-paid tour/excursion", (100, 1500)),
                    ("transfer", "Airport transfer booking", (50, 300)),
                ]
            elif primary_section == "medical_emergency":
                items = [
                    ("er_visit", "Emergency room visit abroad", (1000, 8000)),
                    ("medication", "Prescription medication", (50, 500)),
                    ("ambulance", "Ambulance transport", (500, 3000)),
                    ("follow_up", "Follow-up doctor visit", (100, 500)),
                ]
            else:  # baggage
                items = [
                    ("luggage", "Lost luggage contents", (200, 2000)),
                    ("delayed_essentials", "Essential purchases (delayed baggage)", (50, 500)),
                    ("damaged_item", "Damaged item in transit", (100, 1000)),
                ]

            item = items[i % len(items)]
            amount = self._round_to(self.rng.randint(*item[2]), 25)
            claim["line_items"].append({
                "name": item[0],
                "label": item[1],
                "claimed_amount": amount,
                "actual_amount": amount,
                "section": primary_section,
                "has_receipt": self.rng.random() > 0.2,
            })

    # ─── Fraud Injection ─────────────────────────────────────────────

    def _inject_fraud(self, claim: Dict, policy: Dict):
        """Inject fraud indicators for hard difficulty."""
        num_flags = self.rng.randint(4, 7)
        available = list(pools.FRAUD_INDICATORS)
        self.rng.shuffle(available)

        inception = date.fromisoformat(policy["period_start"])
        incident = date.fromisoformat(claim["incident_date"])
        days_since = (incident - inception).days

        for fraud_tmpl in available[:num_flags]:
            flag = {
                "indicator": fraud_tmpl["type"],
                "severity": fraud_tmpl["severity"],
            }

            # Generate description from template
            if fraud_tmpl["type"] == "timing":
                flag["description"] = fraud_tmpl["description_template"].format(
                    days=days_since, inception=policy["period_start"],
                    claim_date=claim["incident_date"])
            elif fraud_tmpl["type"] == "inflated_values" and claim["line_items"]:
                item = self.rng.choice(claim["line_items"])
                actual = int(item["claimed_amount"] * 0.6)
                item["actual_amount"] = actual
                item["has_receipt"] = True
                flag["description"] = fraud_tmpl["description_template"].format(
                    item=item["label"], claimed=item["claimed_amount"],
                    actual=actual, pct=((item["claimed_amount"] / actual - 1) * 100) if actual > 0 else 100)
            elif fraud_tmpl["type"] == "related_contractor":
                contractor_name = f"{policy['holder_last']} & Sons Construction"
                flag["description"] = fraud_tmpl["description_template"].format(
                    contractor=contractor_name, holder_name=policy["holder_last"])
            elif fraud_tmpl["type"] == "prior_claims":
                flag["description"] = fraud_tmpl["description_template"].format(
                    count=self.rng.randint(2, 4),
                    claim_type=self.insurance_type,
                    years=self.rng.randint(2, 5))
            elif fraud_tmpl["type"] == "items_moved":
                flag["description"] = fraud_tmpl["description_template"].format(
                    items="several large boxes",
                    vehicle=self.rng.choice(["van", "pickup truck", "SUV"]),
                    days_before=self.rng.randint(3, 10))
            elif fraud_tmpl["type"] == "suspicious_fire":
                flag["description"] = fraud_tmpl["description_template"].format(
                    finding="localized and contained burn pattern, inconsistent with reported cause")
            elif fraud_tmpl["type"] == "no_receipts":
                unrecepted = [i for i in claim["line_items"] if not i.get("has_receipt")]
                count = len(unrecepted) or self.rng.randint(2, 5)
                total = sum(i["claimed_amount"] for i in unrecepted) or self.rng.randint(5000, 20000)
                flag["description"] = fraud_tmpl["description_template"].format(
                    count=count, total=total, section="5", threshold=500)
            elif fraud_tmpl["type"] == "no_security":
                flag["description"] = fraud_tmpl["description_template"].format(
                    security_type=self.rng.choice(["alarm system", "security cameras", "motion sensors"]),
                    value=claim.get("total_claimed", 50000))
            elif fraud_tmpl["type"] == "inconsistent_story":
                flag["description"] = fraud_tmpl["description_template"].format(
                    claim_detail="incident occurred at 3 PM",
                    evidence_source="security camera footage",
                    evidence_detail="no activity at the property between 2-5 PM")
            elif fraud_tmpl["type"] == "witness_contradiction":
                witness = f"{self.rng.choice(pools.FIRST_NAMES)} {self.rng.choice(pools.LAST_NAMES)}"
                flag["description"] = fraud_tmpl["description_template"].format(
                    witness_name=witness,
                    witness_statement="I saw the owner at the property that evening, not away as claimed")
            elif fraud_tmpl["type"] == "financial_distress":
                flag["description"] = fraud_tmpl["description_template"].format(
                    financial_detail=self.rng.choice([
                        "policyholder filed for bankruptcy 2 months ago",
                        "3 months of missed mortgage payments",
                        "business owned by policyholder closed last quarter",
                    ]))
            elif fraud_tmpl["type"] == "duplicate_claim":
                flag["description"] = fraud_tmpl["description_template"].format(
                    item=self.rng.choice(claim["line_items"])["label"] if claim["line_items"] else "property",
                    other_insurer=self.rng.choice(["StateFarm", "Allstate", "GEICO", "Progressive"]),
                    other_date=(incident - timedelta(days=self.rng.randint(10, 60))).isoformat())
            else:
                flag["description"] = f"Suspicious pattern detected: {fraud_tmpl['type']}"

            claim["fraud_indicators"].append(flag)

    # ─── Ground Truth Computation ────────────────────────────────────

    def _compute_ground_truth(self, policy: Dict, claim: Dict) -> Dict[str, Any]:
        """Compute deterministic ground truth from structured data."""
        inception = date.fromisoformat(policy["period_start"])
        period_end = date.fromisoformat(policy["period_end"])
        incident = date.fromisoformat(claim["incident_date"])
        filed = date.fromisoformat(claim["filed_date"])

        # Eligibility
        is_eligible = (
            inception <= incident <= period_end
            and policy["premium_status"] in ("paid", "current")
        )
        deadline = policy["conditions"].get("deadline_days", 30)
        filed_in_time = (filed - incident).days <= deadline

        eligibility = {
            "is_eligible": is_eligible and filed_in_time,
            "reason": self._eligibility_reason(is_eligible, filed_in_time, policy, claim),
        }

        # Coverage per item
        item_coverage = {}
        excluded_items = {}
        exclusion_ids = {e["id"] for e in policy["exclusions"]}

        for item in claim["line_items"]:
            name = item["name"]
            section_key = item["section"]

            # Check if item falls under an exclusion
            if section_key.startswith("excluded_"):
                exc_id = section_key.replace("excluded_", "")
                item_coverage[name] = {
                    "covered": False,
                    "reason": f"Excluded: {exc_id}",
                    "amount": item["claimed_amount"],
                }
                excluded_items[name] = item["claimed_amount"]
                continue

            # Find the policy section
            section = policy["sections"].get(section_key)
            if section is None:
                # Try to match section loosely
                section = self._find_section(policy, section_key)

            if section is None:
                item_coverage[name] = {
                    "covered": False,
                    "reason": f"No matching policy section for '{section_key}'",
                    "amount": item["claimed_amount"],
                }
                excluded_items[name] = item["claimed_amount"]
                continue

            # Item is covered
            actual_amount = item.get("actual_amount", item["claimed_amount"])
            rate = section.get("rate", 0.80)

            # Check for sub-item rates (medical)
            if "sub_items" in section:
                for sub_key, sub_info in section["sub_items"].items():
                    if sub_key in name or name in sub_key:
                        rate = sub_info.get("rate", rate)
                        break

            covered_amount = actual_amount * rate
            item_coverage[name] = {
                "covered": True,
                "rate": rate,
                "claimed_amount": item["claimed_amount"],
                "approved_amount": round(covered_amount, 2),
                "section": section_key,
            }

        # Compute total payout
        total_covered = sum(
            ic["approved_amount"] for ic in item_coverage.values() if ic.get("covered")
        )

        # Apply deductibles
        total_deductible = 0
        for section_key, section in policy["sections"].items():
            if "deductible" in section:
                section_items = [
                    ic for name, ic in item_coverage.items()
                    if ic.get("covered") and ic.get("section") == section_key
                ]
                if section_items:
                    total_deductible += section["deductible"]

        payout_before_limit = max(0, total_covered - total_deductible)

        # Apply overall limit (use highest section limit)
        max_limit = max(
            (s.get("limit", float("inf")) for s in policy["sections"].values()),
            default=float("inf"),
        )
        correct_payout = min(payout_before_limit, max_limit)

        # Fraud check
        fraud_flags = claim.get("fraud_indicators", [])
        has_fraud = len(fraud_flags) >= 3  # 3+ flags = deny

        if has_fraud:
            correct_payout = 0.0
            correct_decision = "deny"
        elif excluded_items and correct_payout < claim["total_claimed"] * 0.95:
            correct_decision = "partial_approve"
        elif correct_payout > 0:
            correct_decision = "approve"
        else:
            correct_decision = "deny"

        return {
            "eligibility": eligibility,
            "coverage": {
                "section": self.insurance_type,
                "is_covered": any(ic.get("covered") for ic in item_coverage.values()),
                "reason": f"Claim items checked against {self.insurance_type} policy sections",
                "item_coverage": item_coverage,
            },
            "exclusions": {
                "any_apply": bool(excluded_items),
                "applicable_exclusions": [
                    {"item": name, "exclusion": f"Not covered", "amount_excluded": amt}
                    for name, amt in excluded_items.items()
                ],
            },
            "payout": {
                "claimed_amount": claim["total_claimed"],
                "correct_payout": round(correct_payout, 2),
                "payout_if_no_fraud": round(min(payout_before_limit, max_limit), 2) if has_fraud else round(correct_payout, 2),
                "total_deductible": total_deductible,
                "calculation": self._build_calculation_string(
                    item_coverage, total_deductible, max_limit, correct_payout, has_fraud),
            },
            "fraud_flags": fraud_flags,
            "honeypots": self._generate_honeypots() if has_fraud else [],
            "correct_decision": correct_decision,
            "correct_decision_amount": round(correct_payout, 2),
        }

    def _generate_honeypots(self) -> List[Dict[str, Any]]:
        """Generate honeypot traps for hard/fraud scenarios."""
        honeypot_templates = [
            {
                "name": "fake_weather_excuse",
                "triggers": ["weather", "storm", "natural disaster", "act of god"],
                "hint": "The claim is for theft/fraud, not weather damage. Weather is irrelevant.",
            },
            {
                "name": "fake_third_party_blame",
                "triggers": ["third party", "other driver", "neighbor fault", "someone else"],
                "hint": "The fraud indicators point to the policyholder, not a third party.",
            },
            {
                "name": "fake_maintenance_excuse",
                "triggers": ["maintenance", "routine repair", "scheduled service"],
                "hint": "Maintenance records are unrelated to the claimed incident.",
            },
            {
                "name": "fake_emotional_appeal",
                "triggers": ["hardship", "financial difficulty", "family emergency"],
                "hint": "Emotional circumstances don't change the coverage determination.",
            },
        ]
        num = self.rng.randint(1, 2)
        return self.rng.sample(honeypot_templates, k=min(num, len(honeypot_templates)))

    # ─── Text Rendering ──────────────────────────────────────────────

    def _render_policy(self, policy: Dict) -> str:
        lines = []
        type_label = {
            "auto": "AUTO", "medical": "HEALTH", "home": "HOME", "travel": "TRAVEL"
        }[policy["type"]]

        company = self.rng.choice([
            "ACME", "PINNACLE", "GUARDIAN", "LIBERTY", "SENTINEL",
            "SUMMIT", "ATLAS", "HORIZON", "PREMIER", "NATIONAL"
        ])

        lines.append(f"{company} {type_label} INSURANCE POLICY — Policy #{policy['id']}")
        lines.append(f"Policyholder: {policy['holder_name']}")
        lines.append(f"Policy Period: {policy['period_start']} – {policy['period_end']}")
        lines.append(f"Premium Status: {policy['premium_status'].upper()}")
        lines.append("")

        # Sections
        for i, (key, section) in enumerate(policy["sections"].items(), 1):
            lines.append(f"SECTION {i}: {key.upper().replace('_', ' ')} COVERAGE")
            lines.append(section["description"])
            if "deductible" in section:
                lines.append(f"- Deductible: ${section['deductible']:,}")
            if "limit" in section:
                lines.append(f"- Coverage Limit: ${section['limit']:,}")
            if "rate" in section:
                lines.append(f"- Coverage Rate: {section['rate']*100:.0f}%")
            if "sub_items" in section:
                for sub_key, sub in section["sub_items"].items():
                    detail = f"- {sub['label']}: "
                    if "rate" in sub:
                        detail += f"covered at {sub['rate']*100:.0f}%"
                    if "copay" in sub:
                        detail += f"${sub['copay']} copay"
                    if "session_limit" in sub:
                        detail += f", max {sub['session_limit']} sessions per year"
                    lines.append(detail)
            if "high_value_cap" in section:
                lines.append(f"- High-value items (>$2,500/item) require scheduled endorsement. "
                           f"Unscheduled limited to ${section['high_value_cap']:,}/item.")
            if "covered_reasons" in section:
                lines.append("Covered reasons: " + ", ".join(section["covered_reasons"]))
            if "per_item_cap" in section:
                lines.append(f"- Per-item cap: ${section['per_item_cap']:,}")
            lines.append("")

        # Exclusions
        exc_section = len(policy["sections"]) + 1
        lines.append(f"SECTION {exc_section}: EXCLUSIONS")
        lines.append("The following are NOT covered:")
        for j, exc in enumerate(policy["exclusions"]):
            lines.append(f"  {chr(97+j)}) {exc['text']}")
        lines.append("")

        # Conditions
        cond_section = exc_section + 1
        lines.append(f"SECTION {cond_section}: CONDITIONS")
        if "deadline_days" in policy["conditions"]:
            lines.append(f"- Claims must be reported within {policy['conditions']['deadline_days']} days of the incident")
        if "police_threshold" in policy["conditions"]:
            lines.append(f"- Police report required for claims exceeding ${policy['conditions']['police_threshold']:,}")
        if "pre_auth_required" in policy["conditions"]:
            lines.append("- Pre-authorization required for all inpatient stays and advanced imaging")
        if "proof_of_loss_days" in policy["conditions"]:
            lines.append(f"- Sworn proof of loss required within {policy['conditions']['proof_of_loss_days']} days")
        if "receipt_threshold" in policy["conditions"]:
            lines.append(f"- Receipts required for items exceeding ${policy['conditions']['receipt_threshold']:,}")
        lines.append("- Policyholder must cooperate fully with any investigation")
        lines.append("- Misrepresentation or fraud voids coverage for the entire claim")

        return "\n".join(lines)

    def _render_claim(self, claim: Dict, policy: Dict) -> str:
        lines = []
        lines.append(f"CLAIM SUBMISSION — Claim #{claim['id']}")
        lines.append(f"Claimant: {policy['holder_name']}")
        lines.append(f"Policy: #{policy['id']}")
        lines.append(f"Date of Incident: {claim['incident_date']}")
        lines.append(f"Date Filed: {claim['filed_date']}")
        lines.append("")

        lines.append("INCIDENT DESCRIPTION:")
        city = self.rng.choice(pools.CITIES)
        lines.append(f"On {claim['incident_date']}, {claim['scenario']}.")
        lines.append(f"Location: {self.rng.randint(100,999)} {self.rng.choice(pools.STREETS)}, {city}.")
        lines.append("")

        lines.append("ITEMIZED CHARGES:")
        for i, item in enumerate(claim["line_items"], 1):
            lines.append(f"  {i}. {item['label']}: ${item['claimed_amount']:,.2f}")
        lines.append("")
        lines.append(f"TOTAL CLAIMED: ${claim['total_claimed']:,.2f}")

        return "\n".join(lines)

    def _render_evidence(self, claim: Dict, policy: Dict) -> List[str]:
        evidence = []
        city = self.rng.choice(pools.CITIES)

        # Police/incident report
        if self.insurance_type in ("auto", "home"):
            evidence.append(
                f"Police Report #{self.rng.choice(['WPD','SPD','MPD'])}-{claim['incident_date'][:4]}-"
                f"{self.rng.randint(1000,9999)}: Officers responded to {claim['scenario']}. "
                f"Location: {city}. Report filed {claim['incident_date']}."
            )

        # Repair/medical estimates
        if self.insurance_type == "auto":
            shop = self.rng.choice(pools.AUTO_SHOPS)
            items_desc = ", ".join(f"{i['label']} (${i['claimed_amount']:,.2f})" for i in claim["line_items"][:3])
            evidence.append(f"Repair estimate from {shop}: {items_desc}. Total: ${claim['total_claimed']:,.2f}.")
        elif self.insurance_type == "medical":
            hospital = self.rng.choice(pools.HOSPITALS)
            evidence.append(f"Medical records from {hospital}: {claim['scenario']}. All services rendered in-network.")
        elif self.insurance_type == "home":
            contractor = self.rng.choice(pools.CONTRACTORS)
            evidence.append(f"Contractor estimate from {contractor}: ${claim['total_claimed']:,.2f} for repairs.")

        # Receipts
        receipted = [i for i in claim["line_items"] if i.get("has_receipt")]
        if receipted:
            receipt_desc = ", ".join(f"{i['label']} (${i.get('actual_amount', i['claimed_amount']):,.2f})" for i in receipted[:4])
            evidence.append(f"Receipts provided: {receipt_desc}.")

        unrecepted = [i for i in claim["line_items"] if not i.get("has_receipt")]
        if unrecepted:
            evidence.append(f"No receipts provided for: {', '.join(i['label'] for i in unrecepted)}.")

        # Fraud-related evidence
        for flag in claim.get("fraud_indicators", []):
            evidence.append(flag["description"])

        return evidence

    # ─── Helpers ──────────────────────────────────────────────────────

    def _round_to(self, value: int, nearest: int) -> int:
        return round(value / nearest) * nearest

    def _eligibility_reason(self, eligible: bool, filed_in_time: bool,
                            policy: Dict, claim: Dict) -> str:
        parts = []
        if eligible:
            parts.append("Policy is active and premiums paid")
        else:
            parts.append("Eligibility issue detected")
        if filed_in_time:
            parts.append("Claim filed within deadline")
        else:
            parts.append("Claim filed AFTER deadline")
        if self.difficulty == "hard":
            inception = date.fromisoformat(policy["period_start"])
            incident = date.fromisoformat(claim["incident_date"])
            days = (incident - inception).days
            parts.append(f"Note: only {days} days between policy inception and claim")
        return ". ".join(parts) + "."

    def _find_section(self, policy: Dict, key: str) -> Optional[Dict]:
        """Try to find a matching section by loose matching."""
        for sec_key, sec in policy["sections"].items():
            if sec_key in key or key in sec_key:
                return sec
        return None

    def _build_calculation_string(self, item_coverage: Dict, deductible: float,
                                   limit: float, payout: float, has_fraud: bool) -> str:
        covered = {k: v for k, v in item_coverage.items() if v.get("covered")}
        parts = []
        for name, info in covered.items():
            parts.append(f"{name}: ${info['approved_amount']:,.2f}")

        calc = "Covered items: " + ", ".join(parts) if parts else "No covered items"
        calc += f". Deductible: ${deductible:,.2f}. Limit: ${limit:,.2f}."
        calc += f" Payout: ${payout:,.2f}."
        if has_fraud:
            calc += " DENIED due to fraud indicators."
        return calc

    def _get_scoring_weights(self) -> Dict[str, float]:
        if self.difficulty == "easy":
            return {
                "eligibility": 0.10, "coverage": 0.25, "exclusions": 0.10,
                "payout": 0.30, "fraud": 0.05, "decision": 0.20,
            }
        elif self.difficulty == "medium":
            return {
                "eligibility": 0.10, "coverage": 0.25, "exclusions": 0.15,
                "payout": 0.25, "fraud": 0.05, "decision": 0.20,
            }
        else:  # hard
            return {
                "eligibility": 0.05, "coverage": 0.15, "exclusions": 0.15,
                "payout": 0.15, "fraud": 0.30, "decision": 0.20,
            }
