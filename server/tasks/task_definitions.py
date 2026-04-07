"""
Task definitions for the Insurance Claims Adjudication Environment.

Each task contains:
- A policy document (the rule engine)
- A claim submission (the facts)
- Supporting evidence (additional context)
- Ground truth (correct answers for deterministic grading)
"""

from typing import Any, Dict, List, Optional


def _task_easy() -> Dict[str, Any]:
    """Task 1 (Easy): Straightforward auto collision claim.

    Clear policy, clear incident, no exclusions. Agent needs to verify
    eligibility, confirm coverage, calculate payout, and approve.
    """
    return {
        "task_id": "easy_auto_collision",
        "difficulty": "easy",
        "max_steps": 15,
        "policy_document": """
ACME AUTO INSURANCE POLICY — Policy #POL-2024-78432
Policyholder: Sarah Mitchell
Policy Period: January 1, 2024 – December 31, 2024
Premium Status: PAID IN FULL

SECTION 1: COLLISION COVERAGE
Coverage applies when the insured vehicle sustains damage from a collision
with another vehicle or object, regardless of fault.
- Deductible: $500
- Coverage Limit: $25,000 per incident
- Coverage Rate: 80% of approved amount after deductible

SECTION 2: COMPREHENSIVE COVERAGE
Coverage applies for non-collision damage including theft, vandalism,
natural disasters, and animal strikes.
- Deductible: $250
- Coverage Limit: $25,000 per incident
- Coverage Rate: 100% of approved amount after deductible

SECTION 3: EXCLUSIONS
The following are NOT covered:
- Intentional damage by the policyholder
- Damage while vehicle is used for commercial purposes (rideshare, delivery)
- Damage occurring outside the United States
- Normal wear and tear
- Mechanical breakdown not caused by a covered event

SECTION 4: CONDITIONS
- Claims must be reported within 30 days of the incident
- Police report required for claims exceeding $2,000
- The policyholder must cooperate with any investigation
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #CLM-2024-11205
Claimant: Sarah Mitchell
Policy: #POL-2024-78432
Date of Incident: March 15, 2024
Date Filed: March 18, 2024

INCIDENT DESCRIPTION:
On March 15, 2024, at approximately 3:30 PM, I was driving my 2021 Honda
Civic on Route 9 in Westborough, MA. A vehicle ahead of me stopped suddenly
at a yellow light. I applied my brakes but was unable to stop in time and
collided with the rear of the other vehicle.

DAMAGE DESCRIPTION:
- Front bumper: cracked and needs replacement
- Hood: dented
- Headlight assembly (driver side): broken
- Radiator: damaged and leaking

CLAIMED AMOUNT: $8,500.00

The vehicle is currently at Mike's Auto Body (123 Main St, Westborough, MA).
Repair estimate attached.
""".strip(),
        "supporting_evidence": [
            "Police Report #WPD-2024-0842: Confirms rear-end collision on Route 9, "
            "Westborough. No injuries. Filed March 15, 2024.",
            "Repair Estimate from Mike's Auto Body: Front bumper replacement ($2,200), "
            "hood repair ($1,800), headlight assembly ($1,500), radiator replacement "
            "($3,000). Total: $8,500.00.",
            "Photos: 4 photos showing front-end damage consistent with rear-end collision.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active and paid, incident within policy period",
            },
            "coverage": {
                "section": "collision",
                "is_covered": True,
                "reason": "Collision with another vehicle is covered under Section 1",
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
            },
            "payout": {
                "claimed_amount": 8500.00,
                "deductible": 500.00,
                "coverage_limit": 25000.00,
                "coverage_rate": 0.80,
                "correct_payout": 6400.00,  # (8500 - 500) * 0.80 = 6400
                "calculation": "(8500 - 500) × 0.80 = 6400.00",
            },
            "fraud_flags": [],
            "correct_decision": "approve",
            "correct_decision_amount": 6400.00,
        },
        "scoring_weights": {
            "eligibility": 0.10,
            "coverage": 0.25,
            "exclusions": 0.10,
            "payout": 0.30,
            "fraud": 0.05,
            "decision": 0.20,
        },
    }


def _task_medium() -> Dict[str, Any]:
    """Task 2 (Medium): Medical claim with exclusions and partial coverage.

    Policy has multiple exclusions. Some claimed items are covered, some are
    not. Agent must read carefully and compute a partial payout.
    """
    return {
        "task_id": "medium_medical_exclusions",
        "difficulty": "medium",
        "max_steps": 20,
        "policy_document": """
PINNACLE HEALTH INSURANCE POLICY — Policy #MED-2024-55190
Policyholder: David Chen
Policy Period: July 1, 2023 – June 30, 2024
Premium Status: CURRENT (monthly auto-pay)

SECTION 1: INPATIENT HOSPITAL COVERAGE
Covers medically necessary inpatient hospital stays including:
- Room and board (semi-private rate): covered at 90%
- Surgeon fees: covered at 80%
- Anesthesia: covered at 80%
- Lab work and diagnostics during stay: covered at 100%
- Deductible: $1,000 per admission
- Out-of-pocket maximum: $5,000 per policy year

SECTION 2: OUTPATIENT SERVICES
- Office visits: $30 copay
- Diagnostic imaging (X-ray, MRI): covered at 70%
- Physical therapy: covered at 60%, max 20 sessions per year
- Deductible: $500 per year (separate from inpatient)

SECTION 3: PRESCRIPTION DRUG COVERAGE
- Generic drugs: $10 copay
- Brand-name formulary: $40 copay
- Brand-name non-formulary: 50% coinsurance
- Specialty drugs: 30% coinsurance, max $250 per prescription

SECTION 4: EXCLUSIONS
The following are NOT covered under any section:
a) Cosmetic procedures unless medically necessary due to accident or illness
b) Experimental or investigational treatments not approved by the FDA
c) Services received outside the provider network without prior authorization
d) Pre-existing conditions during the first 6 months of coverage
   (waiting period: July 1, 2023 – December 31, 2023)
e) Dental services (separate dental plan required)
f) Vision correction surgery (LASIK, PRK)
g) Weight loss surgery unless BMI exceeds 40

SECTION 5: CONDITIONS
- Pre-authorization required for all inpatient stays
- Pre-authorization required for MRI/CT scans
- Claims must be submitted within 90 days
- Out-of-network services require prior approval
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #CLM-2024-30847
Claimant: David Chen
Policy: #MED-2024-55190
Date of Service: February 10-14, 2024
Date Filed: February 28, 2024

SUMMARY:
David Chen was admitted to Springfield General Hospital on February 10, 2024,
for an emergency appendectomy. During the stay, additional services were
provided. Pre-authorization was obtained by the hospital on Feb 10 (emergency
admission).

ITEMIZED CHARGES:
1. Emergency room visit and admission: $3,500
2. Appendectomy surgery (surgeon fee): $12,000
3. Anesthesia for surgery: $4,000
4. Hospital room (4 nights, semi-private): $8,000 ($2,000/night)
5. Lab work and blood tests during stay: $1,200
6. Post-operative MRI scan: $2,500
7. Dental crown repair (tooth cracked during intubation): $1,800
8. Post-discharge physical therapy (8 sessions): $2,400 ($300/session)
9. Prescription: Amoxicillin (generic antibiotic): $45
10. Prescription: OxyContin brand-name (pain management): $180

TOTAL CLAIMED: $35,625.00

PROVIDER: Springfield General Hospital (IN-NETWORK)
""".strip(),
        "supporting_evidence": [
            "Hospital admission records: Emergency admission Feb 10, 2024. "
            "Diagnosis: acute appendicitis. Pre-authorization #PA-2024-8891 "
            "obtained same day (emergency basis).",
            "Surgical report: Laparoscopic appendectomy performed Feb 10 by "
            "Dr. Amanda Foster. No complications. Standard procedure.",
            "Radiology report: Post-operative MRI Feb 12 ordered by Dr. Foster "
            "to rule out abscess. Pre-authorization #PA-2024-8903 obtained Feb 11.",
            "Dental note: Patient's left molar (#19) cracked during emergency "
            "intubation on Feb 10. Dr. Lee (dentist) performed crown Feb 13.",
            "Physical therapy records: 8 sessions Feb 20 – Mar 15, 2024. "
            "Post-surgical rehabilitation for core strength recovery.",
            "Pharmacy records: Amoxicillin 500mg (generic), OxyContin 10mg "
            "(brand-name formulary).",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy active, premiums current, incident within policy period. "
                "Pre-existing condition exclusion does not apply (appendicitis is "
                "acute, not pre-existing, and waiting period ended Dec 31, 2023).",
            },
            "coverage": {
                "section": "inpatient",
                "is_covered": True,
                "reason": "Emergency appendectomy is medically necessary inpatient care",
                "item_coverage": {
                    "er_admission": {
                        "covered": True,
                        "section": "inpatient",
                        "rate": 0.90,
                        "amount": 3500,
                    },
                    "surgery": {
                        "covered": True,
                        "section": "inpatient",
                        "rate": 0.80,
                        "amount": 12000,
                    },
                    "anesthesia": {
                        "covered": True,
                        "section": "inpatient",
                        "rate": 0.80,
                        "amount": 4000,
                    },
                    "room_board": {
                        "covered": True,
                        "section": "inpatient",
                        "rate": 0.90,
                        "amount": 8000,
                    },
                    "lab_work": {
                        "covered": True,
                        "section": "inpatient",
                        "rate": 1.00,
                        "amount": 1200,
                    },
                    "mri": {
                        "covered": True,
                        "section": "outpatient",
                        "rate": 0.70,
                        "amount": 2500,
                    },
                    "dental": {
                        "covered": False,
                        "section": "exclusion_e",
                        "reason": "Dental services excluded (Section 4e)",
                        "amount": 1800,
                    },
                    "physical_therapy": {
                        "covered": True,
                        "section": "outpatient",
                        "rate": 0.60,
                        "amount": 2400,
                    },
                    "amoxicillin": {
                        "covered": True,
                        "section": "prescription",
                        "copay": 10,
                        "amount": 45,
                    },
                    "oxycontin": {
                        "covered": True,
                        "section": "prescription",
                        "copay": 40,
                        "amount": 180,
                    },
                },
            },
            "exclusions": {
                "any_apply": True,
                "applicable_exclusions": [
                    {
                        "item": "dental_crown",
                        "exclusion": "Section 4e: Dental services not covered",
                        "amount_excluded": 1800,
                    }
                ],
            },
            "payout": {
                "claimed_amount": 35625.00,
                # Inpatient (after $1000 deductible):
                #   ER: 3500*0.90=3150, Surgery: 12000*0.80=9600,
                #   Anesthesia: 4000*0.80=3200, Room: 8000*0.90=7200,
                #   Lab: 1200*1.00=1200  => subtotal covered = 24350
                #   Inpatient deductible: 1000  => 24350 - 1000 = 23350
                # Outpatient (after $500 deductible):
                #   MRI: 2500*0.70=1750, PT: 2400*0.60=1440 => subtotal = 3190
                #   Outpatient deductible: 500 => 3190 - 500 = 2690
                # Prescriptions (copay model — insurer pays amount minus copay):
                #   Amoxicillin: 45-10=35, OxyContin: 180-40=140 => 175
                # Dental: $0 (excluded)
                # Total payout: 23350 + 2690 + 175 = 26215
                "correct_payout": 26215.00,
                "inpatient_subtotal": 23350.00,
                "outpatient_subtotal": 2690.00,
                "prescription_subtotal": 175.00,
                "excluded_amount": 1800.00,
                "deductible": 1000.00,
                "outpatient_deductible": 500.00,
                "calculation": (
                    "Inpatient: (3500×0.90 + 12000×0.80 + 4000×0.80 + 8000×0.90 "
                    "+ 1200×1.00) - 1000 = 23350. "
                    "Outpatient: (2500×0.70 + 2400×0.60) - 500 = 2690. "
                    "Rx: (45-10) + (180-40) = 175. "
                    "Dental excluded: -1800. "
                    "Total: 23350 + 2690 + 175 = 26215.00"
                ),
            },
            "fraud_flags": [],
            "correct_decision": "partial_approve",
            "correct_decision_amount": 26215.00,
        },
        "scoring_weights": {
            "eligibility": 0.10,
            "coverage": 0.25,
            "exclusions": 0.15,
            "payout": 0.25,
            "fraud": 0.05,
            "decision": 0.20,
        },
    }


def _task_hard() -> Dict[str, Any]:
    """Task 3 (Hard): Suspicious property claim with fraud indicators.

    Claim has multiple red flags: timing suspicious, amounts inflated,
    inconsistent details. Policy language is ambiguous in places. Agent
    must detect fraud, handle ambiguity, and make a nuanced decision.
    """
    return {
        "task_id": "hard_property_fraud",
        "difficulty": "hard",
        "max_steps": 25,
        "policy_document": """
GUARDIAN HOME INSURANCE POLICY — Policy #HOM-2024-91003
Policyholder: Robert Jameson
Policy Period: January 15, 2024 – January 14, 2025
Premium Status: CURRENT
Policy Inception: January 15, 2024

SECTION 1: DWELLING COVERAGE
Covers damage to the insured dwelling from covered perils including:
fire, lightning, windstorm, hail, explosion, smoke, vandalism, and
theft.
- Coverage Limit: $350,000
- Deductible: $2,500
- Coverage Rate: Replacement cost value (100% of approved repairs)

SECTION 2: PERSONAL PROPERTY COVERAGE
Covers personal belongings inside the dwelling.
- Coverage Limit: $100,000 (50% of dwelling coverage unless
  endorsement purchased)
- High-value items (jewelry, art, electronics >$2,500 per item)
  require a scheduled personal property endorsement. Unscheduled
  high-value items are limited to $2,500 per item.
- Deductible: $1,000
- Coverage Rate: Actual cash value (depreciated value) unless
  replacement cost endorsement is purchased

SECTION 3: ADDITIONAL LIVING EXPENSES (ALE)
If the dwelling is uninhabitable due to a covered peril:
- Hotel/temporary housing: reasonable and necessary expenses
- Increased food costs: difference between normal and temporary
- Duration: up to 12 months or until dwelling is repaired
- Coverage Limit: $70,000

SECTION 4: EXCLUSIONS
NOT covered:
a) Flood damage (separate flood policy required)
b) Earthquake damage
c) Gradual deterioration, rust, mold (unless caused by a covered peril)
d) Intentional acts by the policyholder or household members
e) Vacancy: If the dwelling is vacant for more than 60 consecutive
   days, coverage for vandalism and theft is suspended
f) Business property and equipment used for commercial purposes
g) Damage from pets owned by the policyholder

SECTION 5: CONDITIONS
- Claims must be reported within 14 days of discovery
- Policyholder must take reasonable steps to prevent further damage
- Policyholder must provide a sworn proof of loss within 60 days
- Policyholder must cooperate fully with investigation
- Policyholder must provide receipts or proof of purchase for
  personal property claims exceeding $500 per item
- Misrepresentation or fraud voids coverage for the entire claim

SECTION 6: ENDORSEMENTS
No endorsements have been added to this policy.
(No scheduled personal property endorsement)
(No replacement cost endorsement for personal property)
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #CLM-2024-62001
Claimant: Robert Jameson
Policy: #HOM-2024-91003
Date of Incident: February 2, 2024
Date Filed: February 5, 2024

INCIDENT DESCRIPTION:
On the evening of February 2, 2024, I returned home from a weekend trip
to find that my home had been broken into. The back door was forced open.
The intruders ransacked the house and stole numerous valuable items. They
also caused significant damage to the interior — furniture overturned,
walls damaged, and a small fire was set in the kitchen that caused smoke
damage throughout the first floor before self-extinguishing.

CLAIMED ITEMS — PERSONAL PROPERTY:
1. 65" Samsung QLED TV (purchased 2023): $3,200
2. MacBook Pro 16" laptop: $4,500
3. Rolex Submariner watch: $12,000
4. Diamond necklace (wife's): $8,500
5. Vintage guitar collection (3 guitars): $15,000
6. Cash kept in home safe: $5,000
7. Designer clothing and shoes: $6,000
8. Gaming console and games: $1,200

SUBTOTAL PERSONAL PROPERTY: $55,400

CLAIMED ITEMS — DWELLING DAMAGE:
1. Back door replacement and frame repair: $2,800
2. Kitchen fire damage and smoke remediation: $18,500
3. Interior wall repairs and repainting: $8,200
4. Flooring replacement (smoke-damaged): $12,000

SUBTOTAL DWELLING DAMAGE: $41,500

ADDITIONAL LIVING EXPENSES:
- Hotel stay (14 nights during remediation): $4,200
- Increased meal costs: $800

SUBTOTAL ALE: $5,000

TOTAL CLAIMED: $101,900.00
""".strip(),
        "supporting_evidence": [
            "Police Report #SPD-2024-1102: Officers responded Feb 2, 11:45 PM. "
            "Back door forced open. Interior in disarray. Small fire in kitchen "
            "(self-extinguished). No suspects identified. Report notes: 'No alarm "
            "system was active. Neighbors report the home appeared unoccupied for "
            "several days prior.'",
            "Fire Department Report: Called to scene for smoke. Found small "
            "kitchen fire had self-extinguished. Damage limited to kitchen area. "
            "Origin appears to be stovetop — paper/cloth materials ignited. "
            "Investigator note: 'Burn pattern is unusual for a burglary — "
            "localized and contained.'",
            "Receipts provided: Samsung TV receipt ($1,899 from Best Buy, "
            "November 2023). MacBook Pro receipt ($2,499, Apple Store, "
            "September 2023). No receipts for watch, necklace, guitars, "
            "cash, or clothing.",
            "Contractor estimate for dwelling repairs: $41,500 from 'Jameson & "
            "Sons Construction' (NOTE: company shares surname with policyholder).",
            "Hotel receipts: Marriott Courtyard, 14 nights at $300/night = $4,200.",
            "Neighbor statement: 'The Jamesons moved in recently. I noticed "
            "Robert loading several large boxes into a van on January 28. He "
            "said he was taking things to storage.'",
            "Policy inception date: January 15, 2024. Claim date: February 2, "
            "2024. Only 18 days between policy start and claim.",
            "Previous claims history: Robert Jameson had two prior homeowner "
            "claims with different insurers in the past 3 years (both for theft, "
            "both paid out).",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active and premiums current. Claim filed within "
                "14 days. However, the very short time between policy inception "
                "and claim is a red flag.",
            },
            "coverage": {
                "section": "multiple",
                "is_covered": True,
                "reason": "Theft and vandalism are covered perils under Section 1 "
                "and Section 2. ALE covered under Section 3.",
                "item_coverage": {
                    "tv": {
                        "covered": True,
                        "approved_amount": 1899.00,
                        "reason": "Receipt shows actual purchase price of $1,899, "
                        "not claimed $3,200. ACV applies (no replacement cost endorsement).",
                    },
                    "laptop": {
                        "covered": True,
                        "approved_amount": 2499.00,
                        "reason": "Receipt shows $2,499, not claimed $4,500. ACV applies.",
                    },
                    "watch": {
                        "covered": True,
                        "approved_amount": 2500.00,
                        "reason": "No scheduled endorsement — Section 2 limits "
                        "unscheduled high-value items to $2,500 per item. "
                        "No receipt provided.",
                    },
                    "necklace": {
                        "covered": True,
                        "approved_amount": 2500.00,
                        "reason": "Same $2,500 cap for unscheduled high-value items. "
                        "No receipt.",
                    },
                    "guitars": {
                        "covered": True,
                        "approved_amount": 2500.00,
                        "reason": "No receipts. Each guitar >$2,500 would be capped "
                        "individually at $2,500, but claimed as collection. "
                        "Capped at $2,500 total without receipts/endorsement.",
                    },
                    "cash": {
                        "covered": False,
                        "approved_amount": 0,
                        "reason": "Cash is typically limited to $200 in standard "
                        "policies without endorsement. $5,000 claim is excessive "
                        "and unverifiable.",
                    },
                    "clothing": {
                        "covered": True,
                        "approved_amount": 2500.00,
                        "reason": "No receipts for >$500 items as required by "
                        "Section 5. Limited to $2,500 without proof.",
                    },
                    "gaming": {
                        "covered": True,
                        "approved_amount": 1200.00,
                        "reason": "Under $2,500 threshold. Reasonable amount.",
                    },
                    "dwelling_door": {
                        "covered": True,
                        "approved_amount": 2800.00,
                        "reason": "Vandalism/theft damage to dwelling covered.",
                    },
                    "dwelling_fire": {
                        "covered": True,
                        "approved_amount": 18500.00,
                        "reason": "Fire damage covered, though origin is suspicious.",
                    },
                    "dwelling_walls": {
                        "covered": True,
                        "approved_amount": 8200.00,
                        "reason": "Vandalism damage covered.",
                    },
                    "dwelling_flooring": {
                        "covered": True,
                        "approved_amount": 12000.00,
                        "reason": "Smoke damage covered.",
                    },
                    "ale_hotel": {
                        "covered": True,
                        "approved_amount": 4200.00,
                        "reason": "Reasonable temporary housing during repairs.",
                    },
                    "ale_meals": {
                        "covered": True,
                        "approved_amount": 800.00,
                        "reason": "Increased meal costs reasonable for 14 days.",
                    },
                },
            },
            "exclusions": {
                "any_apply": True,
                "applicable_exclusions": [
                    {
                        "item": "cash",
                        "exclusion": "Cash limited to $200 without endorsement",
                        "amount_excluded": 5000,
                    },
                    {
                        "item": "inflated_amounts",
                        "exclusion": "Receipts show lower purchase prices than claimed "
                        "(TV: $1,899 vs $3,200; Laptop: $2,499 vs $4,500). "
                        "ACV applies without replacement cost endorsement.",
                        "amount_excluded": 3302,
                    },
                    {
                        "item": "high_value_caps",
                        "exclusion": "Section 2 caps unscheduled high-value items at "
                        "$2,500 each. No endorsement purchased.",
                        "amount_excluded": 30500,
                    },
                ],
            },
            "payout": {
                "claimed_amount": 101900.00,
                # Personal property (after caps and ACV):
                #   TV: 1899, Laptop: 2499, Watch: 2500, Necklace: 2500,
                #   Guitars: 2500, Cash: 0, Clothing: 2500, Gaming: 1200
                #   Subtotal: 15598, minus $1000 deductible = 14598
                # Dwelling:
                #   Door: 2800, Fire: 18500, Walls: 8200, Floor: 12000
                #   Subtotal: 41500, minus $2500 deductible = 39000
                # ALE: 4200 + 800 = 5000 (no deductible)
                # Total: 14598 + 39000 + 5000 = 58598
                # BUT fraud concerns may warrant denial or hold
                "correct_payout": 0.00,
                "payout_if_no_fraud": 58598.00,
                "personal_property_subtotal": 14598.00,
                "dwelling_subtotal": 39000.00,
                "ale_subtotal": 5000.00,
                "calculation": (
                    "Personal: (1899+2499+2500+2500+2500+0+2500+1200) - 1000 = 14598. "
                    "Dwelling: (2800+18500+8200+12000) - 2500 = 39000. "
                    "ALE: 5000. Total if approved: 58598. "
                    "HOWEVER: Multiple fraud indicators warrant claim denial "
                    "under Section 5 (misrepresentation clause)."
                ),
            },
            "fraud_flags": [
                {
                    "indicator": "timing",
                    "description": "Only 18 days between policy inception and claim — "
                    "extremely suspicious timing.",
                    "severity": "high",
                },
                {
                    "indicator": "inflated_values",
                    "description": "TV claimed at $3,200 (receipt: $1,899). Laptop "
                    "claimed at $4,500 (receipt: $2,499). Systematic inflation.",
                    "severity": "high",
                },
                {
                    "indicator": "related_contractor",
                    "description": "Repair estimate from 'Jameson & Sons Construction' — "
                    "shares surname with policyholder. Potential conflict of interest.",
                    "severity": "medium",
                },
                {
                    "indicator": "prior_claims",
                    "description": "Two prior theft claims with different insurers in "
                    "3 years. Pattern of similar claims.",
                    "severity": "high",
                },
                {
                    "indicator": "items_moved",
                    "description": "Neighbor observed policyholder loading boxes into "
                    "van 5 days before the reported break-in.",
                    "severity": "high",
                },
                {
                    "indicator": "suspicious_fire",
                    "description": "Fire department notes 'unusual burn pattern' — "
                    "localized and contained, inconsistent with burglary arson.",
                    "severity": "medium",
                },
                {
                    "indicator": "no_receipts",
                    "description": "No receipts for highest-value items (watch, "
                    "necklace, guitars) totaling $35,500 in claims.",
                    "severity": "medium",
                },
                {
                    "indicator": "no_alarm",
                    "description": "No alarm system active on a newly insured "
                    "$350,000 property with $100,000 in claimed valuables.",
                    "severity": "low",
                },
            ],
            "correct_decision": "deny",
            "correct_decision_amount": 0.00,
            "decision_reasoning": (
                "Claim denied under Section 5 misrepresentation clause. "
                "Multiple fraud indicators: inflated item values (documented by "
                "receipts contradicting claimed amounts), suspicious timing (18 days "
                "post-inception), pattern of prior theft claims, items apparently "
                "moved before incident, related-party contractor, and suspicious "
                "fire pattern. Recommend referral to Special Investigations Unit."
            ),
        },
        "scoring_weights": {
            "eligibility": 0.05,
            "coverage": 0.15,
            "exclusions": 0.15,
            "payout": 0.15,
            "fraud": 0.30,
            "decision": 0.20,
        },
    }


TASKS = {
    "easy_auto_collision": _task_easy,
    "medium_medical_exclusions": _task_medium,
    "hard_property_fraud": _task_hard,
}


def get_task(task_id: str) -> Dict[str, Any]:
    """Get a task by ID. Raises KeyError if not found."""
    if task_id not in TASKS:
        available = list(TASKS.keys())
        raise KeyError(f"Task '{task_id}' not found. Available: {available}")
    return TASKS[task_id]()
