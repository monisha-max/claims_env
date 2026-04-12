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
            "honeypots": [
                {
                    "name": "fake_weather_report",
                    "triggers": ["weather", "storm", "natural disaster"],
                    "hint": "The claim is for burglary/theft, not weather damage. "
                    "A weather report is irrelevant and planted to mislead.",
                },
                {
                    "name": "fake_appraisal",
                    "triggers": ["appraisal", "appraised value", "market value"],
                    "hint": "The appraisal document was not submitted with the claim. "
                    "Citing it suggests reliance on fabricated evidence.",
                },
            ],
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


def _task_travel() -> Dict[str, Any]:
    """Task 4 (Easy): Trip cancellation due to sudden medical emergency.

    Clear policy, covered reason, straightforward 100% reimbursement of
    non-refundable trip costs. No exclusions apply.
    """
    return {
        "task_id": "easy_travel_cancellation",
        "difficulty": "easy",
        "max_steps": 15,
        "policy_document": """
TRAVELSAFE INSURANCE POLICY — Policy #TRV-2024-30092
Policyholder: Priya Sharma
Policy Period: February 1, 2024 – February 29, 2024 (single-trip)
Premium Status: PAID IN FULL

SECTION 1: TRIP CANCELLATION
Covers 100% of non-refundable, prepaid trip expenses if the trip is
cancelled due to a covered reason before departure.
Covered reasons include:
- Sudden illness or injury of the insured requiring physician-ordered
  travel restriction (must occur after policy purchase)
- Death of insured or immediate family member
- Natural disaster rendering destination uninhabitable
- Jury duty or subpoena issued after policy purchase
- Coverage Limit: $10,000 per trip

SECTION 2: TRIP INTERRUPTION
Covers up to 150% of original trip cost if trip must be cut short due
to a covered reason.
- Coverage Limit: $15,000

SECTION 3: EMERGENCY MEDICAL
Covers emergency medical expenses incurred during travel.
- Coverage Limit: $50,000
- Deductible: $0

SECTION 4: BAGGAGE LOSS AND DELAY
- Loss: up to $2,500 total; $500 per item cap; $250 cap on electronics
- Delay (over 12 hours): $200/day up to $1,000

SECTION 5: EXCLUSIONS
The following are NOT covered:
a) Cancellation due to change of mind or disinclination to travel
b) Pre-existing medical conditions unless the Pre-existing Condition
   Waiver was purchased at the time of policy inception
c) Government-issued travel warnings or advisories (Fear of Travel)
d) Financial default of a travel supplier unless Travel Supplier
   Default coverage is added
e) Participation in extreme sports not listed as covered activities
f) Intentional self-inflicted injury

SECTION 6: CONDITIONS
- Claims must be filed within 60 days of cancellation
- Physician's written statement required for medical cancellations
- Documentation of non-refundability required from all suppliers
- Original receipts required for all claimed expenses
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #TRV-CLM-2024-00481
Claimant: Priya Sharma
Policy: #TRV-2024-30092
Trip Destination: Cancun, Mexico (February 20–27, 2024)
Date of Cancellation: February 18, 2024
Date Filed: February 22, 2024

REASON FOR CANCELLATION:
On February 17, 2024, I fell during a morning jog and fractured my left
ankle (fibula fracture). I visited the emergency room at Boston Medical
Center the same day. My orthopedist, Dr. Kevin Park, has ordered strict
non-weight-bearing rest for a minimum of 6 weeks and has explicitly
stated in writing that I am medically unfit to travel.

NON-REFUNDABLE PREPAID EXPENSES:
1. Round-trip airfare (American Airlines): $1,840.00 (non-refundable fare)
2. Hotel (Excellence Playa Mujeres, 7 nights): $1,960.00 (non-refundable)
3. All-inclusive resort package (Viator): $680.00 (no cancellation refund)

TOTAL CLAIMED: $4,480.00
""".strip(),
        "supporting_evidence": [
            "Emergency Room Report — Boston Medical Center, Feb 17, 2024: "
            "Diagnosis: closed fibula fracture, left ankle. Treatment: splint, "
            "crutches, referral to orthopedics.",
            "Physician Letter — Dr. Kevin Park, MD (Orthopedics), Feb 18, 2024: "
            "'Patient Priya Sharma is medically unable to travel due to acute "
            "fibula fracture. Non-weight-bearing for 6 weeks minimum. Travel is "
            "strictly contraindicated.'",
            "American Airlines cancellation notice: Booking PRSHARM20FEB. "
            "Non-refundable fare. Travel credit issued but cash refund denied. "
            "Ticket value: $1,840.00.",
            "Excellence Playa Mujeres confirmation: Reservation #EXC-78821. "
            "Cancellation Policy: non-refundable after Feb 1, 2024. "
            "Amount forfeited: $1,960.00.",
            "Viator confirmation: Order #VTR-994421. No cancellation refund per "
            "supplier terms. Amount forfeited: $680.00.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active, paid in full, and covers the travel dates. "
                "Claim filed within 60 days of cancellation.",
            },
            "coverage": {
                "section": "trip_cancellation",
                "is_covered": True,
                "reason": "Sudden injury after policy purchase requiring physician-ordered "
                "travel restriction is a covered reason under Section 1.",
                "item_coverage": {
                    "airfare": {"covered": True, "amount": 1840.00},
                    "hotel": {"covered": True, "amount": 1960.00},
                    "tour_package": {"covered": True, "amount": 680.00},
                },
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
            },
            "payout": {
                "claimed_amount": 4480.00,
                "deductible": 0.00,
                "coverage_limit": 10000.00,
                "coverage_rate": 1.00,
                "correct_payout": 4480.00,
                "calculation": "100% of non-refundable trip costs: 1840 + 1960 + 680 = 4480.00",
            },
            "fraud_flags": [],
            "correct_decision": "approve",
            "correct_decision_amount": 4480.00,
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


def _task_pet() -> Dict[str, Any]:
    """Task 5 (Medium): Pet emergency surgery with deductible and reimbursement rate.

    Policy covers accident/illness. Agent must verify no pre-existing condition,
    apply annual deductible, compute 80% reimbursement, and approve.
    """
    return {
        "task_id": "medium_pet_surgery",
        "difficulty": "medium",
        "max_steps": 18,
        "policy_document": """
PAWPROTECT PET INSURANCE POLICY — Policy #PET-2024-17703
Policyholder: James Okafor
Pet: Biscuit (Labrador Retriever, Male, DOB: April 12, 2021)
Policy Period: January 1, 2024 – December 31, 2024
Premium Status: PAID IN FULL

SECTION 1: ACCIDENT AND ILLNESS COVERAGE
Covers veterinary costs for unexpected accidents and illnesses including:
- Emergency examinations and consultations
- Diagnostic imaging (X-rays, ultrasound, MRI, CT scans)
- Laboratory tests and bloodwork
- Surgery and hospitalization
- Specialist referrals
- Prescribed medications (30-day supply per prescription)
- Annual Deductible: $200 (per policy year, not per condition)
- Reimbursement Rate: 80% of eligible expenses after deductible
- Annual Benefit Limit: $10,000

SECTION 2: WELLNESS COVERAGE (ADD-ON — NOT PURCHASED)
Routine and preventive care. Not included in this policy.

SECTION 3: EXCLUSIONS
The following are NOT covered:
a) Pre-existing conditions: Any illness, injury, or symptom documented
   in veterinary records before the policy effective date or during the
   14-day illness waiting period (January 1–14, 2024).
   Accidents are covered from policy effective date (no waiting period).
b) Elective or cosmetic procedures (tail docking, ear cropping)
c) Dental cleaning and prophylaxis (dental disease and injury: covered)
d) Routine/preventive care: vaccinations, flea/tick prevention, wellness
   exams (unless Wellness Add-on purchased)
e) Breeding, pregnancy, whelping costs
f) Experimental or investigational treatments
g) Grooming services

SECTION 4: CONDITIONS
- Claims must be submitted within 180 days of treatment
- All veterinary invoices and medical records must be submitted
- A copy of complete veterinary history may be requested to assess
  pre-existing conditions
- Reimbursement is made directly to the policyholder
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #PET-CLM-2024-09214
Claimant: James Okafor
Policy: #PET-2024-17703
Pet: Biscuit (Labrador Retriever)
Date of Incident: March 8, 2024
Date Filed: March 20, 2024

INCIDENT DESCRIPTION:
On March 8, 2024, Biscuit began vomiting repeatedly and appeared lethargic.
I brought him to City Animal Emergency Hospital, where X-rays revealed a
sock lodged in his small intestine (foreign body obstruction). Emergency
surgery was performed to remove the obstruction. Biscuit recovered well
and was discharged on March 10, 2024.

ITEMIZED VETERINARY INVOICE:
1. Emergency exam and triage: $350.00
2. Abdominal X-rays (series of 3): $420.00
3. Abdominal ultrasound: $280.00
4. Pre-surgical bloodwork: $185.00
5. Foreign body removal surgery: $3,400.00
6. Anesthesia: $480.00
7. Hospitalization (2 nights, ICU monitoring): $920.00
8. IV fluids and supportive care: $310.00
9. Post-operative antibiotics (14-day course): $95.00
10. Pain medication (7-day supply): $80.00
11. Discharge exam and recheck instructions: $80.00

TOTAL INVOICE: $6,600.00
""".strip(),
        "supporting_evidence": [
            "City Animal Emergency Hospital — Veterinary Records, March 8-10, 2024: "
            "Patient: Biscuit, Labrador Retriever, 2 yrs 10 months. Presenting "
            "complaint: repeated vomiting, lethargy. Diagnosis: foreign body "
            "obstruction (textile object — sock) in proximal small intestine. "
            "Procedure: exploratory laparotomy and foreign body removal. Outcome: "
            "uncomplicated recovery. Discharged March 10, 2024.",
            "Prior Veterinary Records — Biscuit (from previous vet, 2022-2023): "
            "Routine wellness exams, vaccinations. No GI conditions documented. "
            "No prior surgeries. No mention of digestive issues or foreign body "
            "incidents.",
            "Policy deductible status: $0 of $200 annual deductible has been used "
            "prior to this claim (first claim of policy year 2024).",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy active and paid. Claim filed within 180 days. "
                "Biscuit is the insured pet.",
            },
            "coverage": {
                "section": "accident_illness",
                "is_covered": True,
                "reason": "Foreign body ingestion is an accident. All treatment items "
                "(exam, imaging, surgery, hospitalization, medications) are covered "
                "under Section 1.",
                "item_coverage": {
                    "emergency_exam": {"covered": True, "amount": 350.00},
                    "xrays": {"covered": True, "amount": 420.00},
                    "ultrasound": {"covered": True, "amount": 280.00},
                    "bloodwork": {"covered": True, "amount": 185.00},
                    "surgery": {"covered": True, "amount": 3400.00},
                    "anesthesia": {"covered": True, "amount": 480.00},
                    "hospitalization": {"covered": True, "amount": 920.00},
                    "iv_fluids": {"covered": True, "amount": 310.00},
                    "antibiotics": {"covered": True, "amount": 95.00},
                    "pain_meds": {"covered": True, "amount": 80.00},
                    "recheck_exam": {"covered": True, "amount": 80.00},
                },
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
            },
            "payout": {
                "claimed_amount": 6600.00,
                "deductible": 200.00,
                "coverage_limit": 10000.00,
                "coverage_rate": 0.80,
                "correct_payout": 5120.00,  # (6600 - 200) * 0.80 = 6400 * 0.80 = 5120
                "calculation": "(6600 - 200) × 0.80 = 6400 × 0.80 = 5120.00",
            },
            "fraud_flags": [],
            "correct_decision": "approve",
            "correct_decision_amount": 5120.00,
        },
        "scoring_weights": {
            "eligibility": 0.10,
            "coverage": 0.25,
            "exclusions": 0.15,
            "payout": 0.30,
            "fraud": 0.05,
            "decision": 0.15,
        },
    }


def _task_life() -> Dict[str, Any]:
    """Task 6 (Medium): Life insurance death benefit claim.

    Agent must verify policy is active, confirm cause of death is covered,
    confirm contestability period has passed, and approve full death benefit.
    """
    return {
        "task_id": "medium_life_benefit",
        "difficulty": "medium",
        "max_steps": 18,
        "policy_document": """
HORIZON TERM LIFE INSURANCE POLICY — Policy #LIFE-2021-44782
Insured: Marcus Williams (DOB: July 14, 1978)
Beneficiary: Angela Williams (Spouse)
Death Benefit: $500,000
Policy Period: March 1, 2021 – February 28, 2031 (10-year term)
Monthly Premium: $185.00 (auto-pay, bank account on file)
Premium Status: CURRENT (last payment: April 1, 2024)

SECTION 1: DEATH BENEFIT
Upon the death of the Insured during the policy term, the Company will
pay the Death Benefit of $500,000 to the named Beneficiary, subject to
the terms and conditions of this policy.

SECTION 2: CONTESTABILITY PERIOD
During the first two (2) years of this policy (March 1, 2021 –
February 28, 2023), the Company reserves the right to contest a claim
and void this policy if the application contained a material
misrepresentation. After the contestability period, the policy is
incontestable except for non-payment of premiums.

Suicide Clause: Death by suicide within the first two (2) years is
excluded. After the two-year period, suicide is a covered cause of death.

SECTION 3: EXCLUSIONS
The following are NOT covered at any time:
a) Death resulting directly from participation in the commission of a
   felony
b) Death resulting from war, declared or undeclared, or armed conflict
   while on active military duty
c) Non-payment of premiums (policy lapses after 31-day grace period)

SECTION 4: BENEFICIARY PROVISIONS
- The named beneficiary may be changed by the policyholder at any time
  prior to death with written notice to the Company
- If the beneficiary predeceases the insured and no contingent
  beneficiary is named, proceeds are paid to the insured's estate
- Lump sum payment; no structured settlement without written election

SECTION 5: CLAIM CONDITIONS
- Claim must be filed within one (1) year of the date of death
- Required documentation:
  (a) Certified copy of death certificate
  (b) Completed Claimant's Statement form
  (c) Proof of beneficiary identity (government-issued ID)
  (d) Proof of relationship (marriage certificate for spouse beneficiary)
- Company may request additional documentation including medical records
  if death occurs within the contestability period
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #LIFE-CLM-2024-00772
Claimant: Angela Williams (Beneficiary/Spouse)
Policy: #LIFE-2021-44782
Insured: Marcus Williams
Date of Death: March 28, 2024
Date Filed: April 10, 2024

CIRCUMSTANCES OF DEATH:
Marcus Williams suffered a sudden cardiac arrest at his home on the
evening of March 28, 2024. Emergency services were called but were
unable to resuscitate him. He was pronounced dead at 9:47 PM at
St. Vincent's Medical Center.

DOCUMENTS SUBMITTED:
1. Certified death certificate — State of Connecticut, issued April 2, 2024
2. Completed Claimant's Statement (form CL-1 signed by Angela Williams)
3. Copy of marriage certificate (Williams/Rodriguez, married June 4, 2005)
4. Angela Williams driver's license (CT DL #A12345678)
5. Autopsy report (requested by Angela Williams from medical examiner)

CLAIMED AMOUNT: $500,000 (full death benefit)
""".strip(),
        "supporting_evidence": [
            "Certified Death Certificate — State of Connecticut: Decedent: Marcus "
            "Williams, DOB July 14, 1978. Date of Death: March 28, 2024. "
            "Cause of Death: Acute myocardial infarction (cardiac arrest). "
            "Manner of Death: Natural. Signed by Medical Examiner Dr. Susan Park.",
            "Autopsy Report — Office of the Chief Medical Examiner, CT: Examination "
            "reveals severe coronary artery disease with acute plaque rupture of the "
            "left anterior descending artery. No evidence of trauma or external cause. "
            "Manner of death: Natural.",
            "Premium Payment History: Policy #LIFE-2021-44782. Premiums paid "
            "continuously from March 2021 through April 2024. No lapses. Last "
            "payment: April 1, 2024 ($185.00 via auto-pay).",
            "Marriage Certificate: Commonwealth of Connecticut. Marcus D. Williams "
            "and Angela M. Rodriguez married June 4, 2005. Certificate #2005-CT-44821.",
            "Policy contestability period: Expired February 28, 2023. Death occurred "
            "March 28, 2024 — over 13 months after end of contestability period.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active with current premiums. Insured died within "
                "policy term. Claim filed within 1 year of death (13 days after death). "
                "Angela Williams is the named beneficiary.",
            },
            "coverage": {
                "section": "death_benefit",
                "is_covered": True,
                "reason": "Death from natural cause (acute myocardial infarction) is "
                "covered. Contestability period expired Feb 28, 2023 — death occurred "
                "13+ months after that. No exclusions apply.",
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
            },
            "payout": {
                "claimed_amount": 500000.00,
                "deductible": 0.00,
                "coverage_limit": 500000.00,
                "coverage_rate": 1.00,
                "correct_payout": 500000.00,
                "calculation": "Full death benefit: $500,000 lump sum to named beneficiary.",
            },
            "fraud_flags": [],
            "correct_decision": "approve",
            "correct_decision_amount": 500000.00,
        },
        "scoring_weights": {
            "eligibility": 0.15,
            "coverage": 0.20,
            "exclusions": 0.20,
            "payout": 0.20,
            "fraud": 0.05,
            "decision": 0.20,
        },
    }


def _task_liability() -> Dict[str, Any]:
    """Task 7 (Medium): Third-party personal injury liability claim.

    A guest is injured on the policyholder's property. Agent must verify
    liability coverage applies, confirm no exclusions, compute total payout
    within policy limits, and approve documented economic damages.
    """
    return {
        "task_id": "medium_liability_injury",
        "difficulty": "medium",
        "max_steps": 20,
        "policy_document": """
HOMESHIELD PERSONAL LIABILITY INSURANCE — Policy #LIA-2024-28810
Policyholder: Thomas Brady
Property: 44 Elm Street, Hartford, CT
Policy Period: January 1, 2024 – December 31, 2024
Premium Status: PAID IN FULL

SECTION 1: PERSONAL LIABILITY COVERAGE
Pays damages the policyholder is legally obligated to pay due to bodily
injury or property damage caused by an occurrence on the insured premises.
- Coverage Limit: $300,000 per occurrence
- Defense costs: covered in addition to the liability limit
- Deductible: $0 (no deductible on liability claims)

SECTION 2: MEDICAL PAYMENTS TO OTHERS
Pays reasonable medical expenses for bodily injury to a third party on
the insured premises, regardless of legal liability (no-fault basis).
- Coverage Limit: $5,000 per person per occurrence
- Deductible: $0

SECTION 3: COVERED DAMAGES UNDER PERSONAL LIABILITY
When liability is established, the following damages are covered:
a) Medical expenses (hospital, surgical, ambulance, rehabilitation)
b) Lost wages resulting directly from the injury (with employer
   verification)
c) Physical therapy and ongoing rehabilitation
d) General damages (pain and suffering) as part of a settled or
   adjudicated claim
All covered damages are subject to the $300,000 per-occurrence limit.

SECTION 4: EXCLUSIONS
NOT covered under this policy:
a) Intentional or criminal acts by the policyholder or household members
b) Bodily injury to the policyholder, resident family members, or
   regular household employees
c) Business activities conducted on the premises (home office, daycare,
   retail)
d) Contractual liability assumed by agreement
e) Motorized vehicles (covered under auto policy)
f) Workers' compensation claims by household employees

SECTION 5: CONDITIONS
- Policyholder must notify the insurer promptly of any occurrence
- Policyholder must not admit liability or make any payment without
  prior written consent of the insurer
- Policyholder must cooperate with investigation and legal proceedings
- Claimant must provide medical records and bills to support all damages
- Lost wages require a signed statement from the employer
""".strip(),
        "claim_submission": """
THIRD-PARTY CLAIM — Claim #LIA-CLM-2024-03317
Claimant: Patricia Novak (third party)
Insured: Thomas Brady (policyholder)
Policy: #LIA-2024-28810
Date of Incident: January 14, 2024
Date Filed (by insured): January 17, 2024

INCIDENT DESCRIPTION:
On January 14, 2024, at approximately 5:30 PM, Patricia Novak arrived
at 44 Elm Street as a dinner guest of Thomas Brady. Upon approaching the
front door, she slipped on an icy section of the walkway, fell, and
sustained a fracture of her right wrist. Photographs taken at the scene
confirm the walkway was iced over with no ice-melt salt or sand applied.
Thomas Brady has acknowledged that he had not treated the walkway that day.

CLAIMED DAMAGES:
1. Emergency room visit: $2,800.00
2. Orthopedic consultation and follow-up (3 visits): $1,650.00
3. Wrist fracture surgery (open reduction, internal fixation): $12,400.00
4. Surgical facility and anesthesia fees: $3,800.00
5. Physical therapy (10 sessions): $2,200.00
6. Lost wages (8 weeks, unable to perform job duties as court reporter):
   $6,240.00 ($780/week × 8 weeks)
7. Pain and suffering: $22,000.00

TOTAL CLAIMED: $51,090.00
""".strip(),
        "supporting_evidence": [
            "Emergency Room Report — Hartford Hospital, Jan 14, 2024: Patient "
            "Patricia Novak, DOB March 3, 1972. Presenting complaint: fall on ice. "
            "Diagnosis: displaced distal radius fracture, right wrist. Treatment: "
            "splinting, referral to orthopedics for surgical evaluation.",
            "Orthopedic Surgical Report — Dr. Daniel Kim, MD: Open reduction and "
            "internal fixation (ORIF) performed Jan 19, 2024. Hardware placed to "
            "stabilize fracture. Estimated 8-week recovery before return to work.",
            "Physical Therapy Records: 10 sessions (Feb 5 – Mar 8, 2024). Goal: "
            "restore wrist range of motion and grip strength post-ORIF. $220/session.",
            "Employer Verification Letter — Hartford Superior Court: Patricia Novak "
            "is employed as a certified court reporter earning $780/week. Unable to "
            "perform duties from Jan 14 to Mar 8, 2024 (8 weeks). Total lost wages: "
            "$6,240.00.",
            "Photographs (6 images) — Taken by Thomas Brady, Jan 14, 2024: Show "
            "icy front walkway with no salt or sand. No visible attempts to treat ice.",
            "Statement of Thomas Brady: 'I had not treated the front walkway on "
            "January 14. I was aware it was cold and slippery. I should have "
            "salted it before guests arrived. I accept responsibility.'",
            "Medical bills summary: ER $2,800 + Ortho visits $1,650 + Surgery "
            "$12,400 + Facility/anesthesia $3,800 + PT $2,200 = $22,850 total "
            "medical expenses.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active and paid. Incident on insured premises "
                "within policy period. Reported within reasonable time (3 days).",
            },
            "coverage": {
                "section": "personal_liability",
                "is_covered": True,
                "reason": "Third-party bodily injury on insured premises caused by "
                "policyholder negligence (failure to treat icy walkway) is covered "
                "under Section 1. Medical payments (Section 2) also apply up to "
                "$5,000 on a no-fault basis.",
                "item_coverage": {
                    "medical_expenses": {
                        "covered": True,
                        "amount": 22850.00,
                        "reason": "All medical expenses (ER, surgery, PT) are covered "
                        "under Section 3a. Total $22,850.",
                    },
                    "lost_wages": {
                        "covered": True,
                        "amount": 6240.00,
                        "reason": "Lost wages with employer verification covered "
                        "under Section 3b.",
                    },
                    "pain_and_suffering": {
                        "covered": True,
                        "amount": 22000.00,
                        "reason": "General damages covered under Section 3d as part "
                        "of settled claim.",
                    },
                },
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
            },
            "payout": {
                "claimed_amount": 51090.00,
                "deductible": 0.00,
                "coverage_limit": 300000.00,
                "coverage_rate": 1.00,
                "correct_payout": 51090.00,
                "calculation": (
                    "Medical: 22850 + Lost wages: 6240 + Pain & suffering: 22000 "
                    "= 51090. All within $300,000 per-occurrence limit. No deductible."
                ),
            },
            "fraud_flags": [],
            "correct_decision": "approve",
            "correct_decision_amount": 51090.00,
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


def _task_flood() -> Dict[str, Any]:
    """Task 8 (Hard): Flood damage on a policy that excludes flood.

    Policyholder has standard homeowner policy only (no flood endorsement).
    Damage was caused by storm drainage backup — which is classified as
    flood, not a covered internal plumbing failure. Agent must distinguish
    covered water damage (burst pipe) from excluded flood water.
    """
    return {
        "task_id": "hard_flood_exclusion",
        "difficulty": "hard",
        "max_steps": 25,
        "policy_document": """
GUARDIAN HOME INSURANCE POLICY — Policy #HOM-2024-55021
Policyholder: Linda Marsh
Property: 18 Riverside Drive, Baton Rouge, LA
Policy Period: January 1, 2024 – December 31, 2024
Premium Status: CURRENT
Flood Insurance: NOT PURCHASED (no flood endorsement on file)

SECTION 1: DWELLING COVERAGE — COVERED PERILS
The following perils are covered when they cause sudden and accidental damage:
- Fire and smoke
- Lightning
- Windstorm and hail
- Explosion
- Vandalism and malicious mischief
- Theft
- Weight of ice, snow, or sleet
- Falling objects
- Sudden and accidental discharge or overflow of water or steam
  from within a plumbing, heating, air conditioning, or automatic
  fire protective sprinkler system, or from a household appliance
  (PLUMBING SYSTEM COVERAGE)
- Coverage Limit: $280,000
- Deductible: $1,500

SECTION 2: PERSONAL PROPERTY COVERAGE
Coverage for personal belongings damaged by a covered peril.
- Coverage Limit: $80,000
- Deductible: $1,000

SECTION 3: ADDITIONAL LIVING EXPENSES
Temporary housing and meals if dwelling is uninhabitable due to covered
peril.
- Coverage Limit: $40,000

SECTION 4: EXCLUSIONS — EXPRESSLY EXCLUDED PERILS
The following are NOT covered under any section of this policy:
a) FLOOD: Surface water, waves, tidal water, overflow of a body of
   water, storm drain backup or overflow, sewer backup (unless sewer
   backup endorsement purchased), storm surge. Water that enters the
   home through any opening caused by flood is not covered even if
   wind or rain contributed to the opening. A separate flood insurance
   policy through NFIP or a private flood insurer is required.
b) EARTHQUAKE and earth movement
c) Mold, fungus, wet rot resulting from flood or long-term moisture
d) Gradual water intrusion through foundation cracks, windows, or doors
   due to exterior water pressure
e) Sewer or drain backup (no endorsement purchased)
f) Power failure (damage caused by power outage off-premises)

SECTION 5: PLUMBING SYSTEM DEFINED
For purposes of Section 1, a "plumbing system" includes pipes, faucets,
valves, water heater, and fixtures that are part of the interior water
supply or drainage network. It does NOT include:
- Sump pumps (a sump pump failure caused by external flood water
  entering the sump pit is classified as flood, not plumbing failure)
- Outdoor drainage systems or municipal storm drains
- Gutters and downspouts

SECTION 6: CONDITIONS
- Claims must be reported within 14 days of the loss
- Policyholder must mitigate further damage
- A sworn proof of loss must be submitted within 60 days
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #HOM-CLM-2024-07741
Claimant: Linda Marsh
Policy: #HOM-2024-55021
Date of Loss: August 19, 2024
Date Filed: August 23, 2024

INCIDENT DESCRIPTION:
On August 19, 2024, Tropical Storm Calvin brought extremely heavy
rainfall to the Baton Rouge area (approximately 8 inches of rain in
18 hours). During the storm, my basement flooded with approximately
2.5 feet of water. My sump pump was running continuously but could not
keep up with the water volume. By morning, the basement was completely
flooded.

I believe the cause of the flood was my sump pump failing to handle the
volume, which is a plumbing system failure covered under Section 1 of
my policy.

CLAIMED DAMAGES:
Basement water damage:
1. Finished basement drywall (full replacement): $14,200
2. Basement flooring (tile, fully submerged): $8,600
3. HVAC system (furnace and air handler submerged): $11,400
4. Water heater (submerged): $1,800
5. Electrical panel damage (water intrusion): $4,200
6. Personal property (furniture, electronics, appliances): $18,500
7. Mold remediation (already visible within 3 days): $6,800

TOTAL CLAIMED: $65,500.00
""".strip(),
        "supporting_evidence": [
            "National Weather Service Report — August 19, 2024, Baton Rouge, LA: "
            "Tropical Storm Calvin produced 7.8 inches of rainfall over 18 hours. "
            "Widespread flooding reported across East Baton Rouge Parish. "
            "Multiple streets and neighborhoods reported under water. Flash flood "
            "warnings in effect from 6 AM to 10 PM.",
            "East Baton Rouge Parish Emergency Management: Declared local state "
            "of emergency Aug 19, 2024. Approximately 1,200 homes reported flooding "
            "in the Riverside Drive area due to storm drainage overflow.",
            "Plumber Inspection Report — Ace Plumbing, Aug 21, 2024: "
            "'Inspected sump pump and pit at 18 Riverside Drive. Sump pump is "
            "mechanically functional — motor and float switch are intact and "
            "operating normally. The pump was overwhelmed by volume. Water in "
            "the sump pit was sourced from exterior storm drainage backing into "
            "the foundation drain tile system, not from any interior plumbing "
            "failure. No burst pipes found anywhere in the home. Water entered "
            "the basement from the exterior drainage and window wells.'",
            "Neighbor statements (3): Confirm that multiple homes on Riverside "
            "Drive experienced similar basement flooding during the storm. 'The "
            "whole street flooded — it was clearly the storm drains overflowing.'",
            "Photographs (12 images): Show basement water line at 2.5 feet, "
            "damage to drywall, flooring, and equipment. Water line consistent "
            "with exterior flood entry through window wells and foundation drain "
            "tile, not interior pipe burst.",
            "Insurance policy endorsement records: Standard homeowner policy "
            "only. No flood endorsement. No sewer backup endorsement. "
            "Policyholder was offered flood insurance endorsement at renewal "
            "in January 2024 and declined.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy is active and premiums current. Claim filed within "
                "14 days (4 days after loss).",
            },
            "coverage": {
                "section": "exclusion_flood",
                "is_covered": False,
                "reason": "Water damage was caused by external storm drainage backup "
                "and surface flooding from Tropical Storm Calvin — this is flood under "
                "Section 4a. Plumber confirmed no burst pipes; sump pump was "
                "mechanically functional but overwhelmed by external flood water. "
                "Section 5 explicitly states that sump pump failure caused by external "
                "flood water is classified as flood, not plumbing failure.",
            },
            "exclusions": {
                "any_apply": True,
                "applicable_exclusions": [
                    {
                        "item": "all_damage",
                        "exclusion": "Section 4a: Flood exclusion. Storm drainage overflow, "
                        "storm surge, and surface water entry are expressly excluded. "
                        "No flood endorsement was purchased.",
                        "amount_excluded": 65500.00,
                    },
                    {
                        "item": "mold",
                        "exclusion": "Section 4c: Mold resulting from flood is excluded.",
                        "amount_excluded": 6800.00,
                    },
                ],
            },
            "payout": {
                "claimed_amount": 65500.00,
                "deductible": 1500.00,
                "coverage_limit": 280000.00,
                "coverage_rate": 0.00,
                "correct_payout": 0.00,
                "calculation": (
                    "Flood exclusion (Section 4a) applies to all claimed damage. "
                    "Sump pump overwhelmed by external storm water ≠ plumbing system "
                    "failure (Section 5). No covered peril triggered. Payout: $0."
                ),
            },
            "fraud_flags": [
                {
                    "indicator": "misclassification_attempt",
                    "description": "Policyholder characterizes sump pump overwhelm as "
                    "'plumbing failure' to invoke coverage. Plumber's report and "
                    "NWS data confirm external flood origin.",
                    "severity": "medium",
                },
                {
                    "indicator": "declined_flood_coverage",
                    "description": "Records show policyholder declined flood insurance "
                    "endorsement at January 2024 renewal.",
                    "severity": "low",
                },
            ],
            "correct_decision": "deny",
            "correct_decision_amount": 0.00,
            "decision_reasoning": (
                "Claim denied under Section 4a (Flood Exclusion). All damage was "
                "caused by storm drainage overflow and surface water intrusion during "
                "Tropical Storm Calvin — a flood event. The sump pump was not a "
                "covered plumbing failure; it was overwhelmed by external flood water "
                "(confirmed by licensed plumber). No flood or sewer backup endorsement "
                "was purchased. Policyholder should file with NFIP flood insurer if "
                "a separate flood policy was obtained."
            ),
            "honeypots": [
                {
                    "name": "fake_plumbing_coverage",
                    "triggers": ["plumbing failure", "internal plumbing", "pipe burst"],
                    "hint": "The damage is from external flooding, not internal plumbing. "
                    "The plumber's report confirms the sump pump was overwhelmed by "
                    "external flood water.",
                },
            ],
        },
        "scoring_weights": {
            "eligibility": 0.05,
            "coverage": 0.20,
            "exclusions": 0.25,
            "payout": 0.15,
            "fraud": 0.15,
            "decision": 0.20,
        },
    }


def _task_disability() -> Dict[str, Any]:
    """Task 9 (Hard): Long-term disability claim with elimination period,
    own-occupation definition, and pre-existing condition question.

    Agent must calculate the 90-day elimination period, correctly apply
    the own-occupation definition (first 24 months), determine that the
    pre-existing condition exclusion has expired, and approve the claim.
    """
    return {
        "task_id": "hard_disability_claim",
        "difficulty": "hard",
        "max_steps": 25,
        "policy_document": """
STEADFAST LONG-TERM DISABILITY INSURANCE — Policy #DIS-2022-19034
Insured: Dr. Elena Vasquez
Occupation: Orthopedic Surgeon
Policy Effective Date: June 1, 2022
Monthly Benefit: $6,500
Benefit Period: To age 65
Premium Status: CURRENT (monthly auto-pay)

SECTION 1: DEFINITION OF TOTAL DISABILITY
The definition of Total Disability changes over the benefit period:

OWN OCCUPATION PERIOD (First 24 months of benefit payments):
The Insured is unable to perform the material and substantial duties of
their OWN OCCUPATION — the specific occupation in which the Insured was
engaged immediately before the disability began — even if able to work
in another occupation.

ANY OCCUPATION PERIOD (After 24 months of benefit payments):
The Insured is unable to perform the duties of ANY occupation for which
they are reasonably suited by education, training, or experience.

SECTION 2: PARTIAL DISABILITY BENEFIT
If the Insured returns to work but earns between 40% and 80% of their
pre-disability income, a partial (proportional) disability benefit is
payable:
Partial Benefit = Monthly Benefit × (Income Loss % / Pre-disability Income)
If earning LESS than 40% of pre-disability income, the Insured is
considered Totally Disabled and the full Monthly Benefit is payable.

SECTION 3: ELIMINATION PERIOD
Benefits begin after a 90-day elimination period from the onset of
disability. No benefits are payable during the elimination period.
The elimination period must be served only once per disability.

SECTION 4: PRE-EXISTING CONDITION EXCLUSION
A condition is Pre-Existing if, within the 12-month period immediately
before the Policy Effective Date (i.e., June 1, 2021 – May 31, 2022),
the Insured:
(a) received medical treatment, consultation, or care for the condition;
  OR
(b) was prescribed medication for the condition; OR
(c) had symptoms that a reasonable person would seek treatment for.

A Pre-Existing condition is excluded from coverage for the first 12
months of the policy (June 1, 2022 – May 31, 2023). After May 31, 2023,
no pre-existing condition exclusion applies.

SECTION 5: EXCLUSIONS (AT ALL TIMES)
NOT covered under any circumstance:
a) Disability resulting from intentional self-inflicted injury
b) Disability arising during active military service
c) Disability resulting from committing or attempting a felony
d) Disability due to substance abuse unless enrolled in a supervised
   rehabilitation program

SECTION 6: BENEFIT PAYMENT CONDITIONS
- Written claim must be filed within 30 days of end of elimination period
- Attending Physician Statement (APS) required from treating specialist
- Proof of pre-disability income (last 12 months of tax returns or
  employer verification)
- Ongoing proof of continued disability required every 90 days
- Pre-disability monthly income for benefit calculation:
  Average monthly income over last 24 months = $16,250/month
""".strip(),
        "claim_submission": """
CLAIM SUBMISSION — Claim #DIS-CLM-2024-00561
Claimant: Dr. Elena Vasquez
Policy: #DIS-2022-19034
Occupation at Time of Disability: Orthopedic Surgeon, Hartford Orthopedic Group
Date Disability Began: September 15, 2023
Claim Filed: January 10, 2024

DESCRIPTION OF DISABILITY:
In August 2023, I began experiencing worsening pain, numbness, and loss of
dexterity in both hands. On September 15, 2023, I was diagnosed by
Dr. Robert Singh (hand specialist) with severe bilateral carpal tunnel
syndrome and trigger finger affecting the right index and middle fingers.
Dr. Singh has stated in writing that I am unable to safely perform surgical
procedures due to the risk of loss of motor control during surgery.

Since September 15, 2023, I have not performed any surgical procedures.
I have continued to see patients in a limited non-surgical capacity
(consultations and follow-up visits only) and have been earning
approximately $4,000/month in this reduced role, compared to my
pre-disability income of $16,250/month.

REQUESTED BENEFIT: $6,500/month beginning December 14, 2023
(90 days after disability onset of September 15, 2023)

DOCUMENTS ATTACHED:
1. Attending Physician Statement from Dr. Robert Singh
2. EMG/nerve conduction study results (Sept 18, 2023)
3. Prior 24-month income documentation
4. Employer verification of reduced duties and earnings
""".strip(),
        "supporting_evidence": [
            "Attending Physician Statement — Dr. Robert Singh, MD (Hand Surgery "
            "Specialist), December 20, 2023: 'Dr. Vasquez has severe bilateral "
            "carpal tunnel syndrome (confirmed by EMG, September 18, 2023) with "
            "superimposed trigger finger, right hand. She is unable to perform "
            "surgical procedures safely. Surgery requires sustained fine motor "
            "control and grip force that she can no longer provide. She is "
            "permanently restricted from operative work. She can perform "
            "non-surgical medical consultations.'",
            "EMG / Nerve Conduction Study — Hartford Neurology, September 18, 2023: "
            "Bilateral median nerve compression consistent with severe carpal tunnel "
            "syndrome. Right hand shows additional findings consistent with trigger "
            "finger at the flexor digitorum superficialis.",
            "Complete Veterinary and Medical History — Dr. Vasquez: "
            "August 14, 2022: Annual physical exam — note reads 'mild bilateral "
            "wrist discomfort reported by patient, attributed to surgical workload. "
            "No treatment recommended. No diagnosis made. Patient declined referral.' "
            "No other wrist/hand entries until September 2023.",
            "Income Documentation (24 months, Jan 2022 – Dec 2023): W-2 and K-1 "
            "from Hartford Orthopedic Group. Average monthly income: $16,250. "
            "Post-disability reduced income (Oct–Dec 2023): $4,000/month.",
            "Hartford Orthopedic Group — Employer Statement: 'Dr. Vasquez has been "
            "relieved of all surgical responsibilities effective September 15, 2023. "
            "She currently performs consultation and non-operative follow-up only. "
            "Her compensation has been reduced accordingly to $4,000/month.'",
            "Policy timeline: Policy effective June 1, 2022. Pre-existing exclusion "
            "window: June 1, 2021 – May 31, 2022. Exclusion expires: May 31, 2023. "
            "Disability onset: September 15, 2023 — over 3 months after exclusion "
            "expiry. Elimination period: Sept 15 + 90 days = December 14, 2023.",
        ],
        "ground_truth": {
            "eligibility": {
                "is_eligible": True,
                "reason": "Policy active with current premiums. Claim filed January 10, "
                "2024 — within 30 days of end of elimination period (Dec 14, 2023). "
                "Dr. Vasquez is the insured.",
            },
            "coverage": {
                "section": "own_occupation_disability",
                "is_covered": True,
                "reason": "Own occupation period applies (disability month 3 at claim "
                "filing, well within first 24 months). Surgery is a material and "
                "substantial duty of an orthopedic surgeon. Dr. Vasquez is unable "
                "to perform surgery due to bilateral carpal tunnel and trigger finger "
                "(confirmed by EMG). The fact that she can perform consultations is "
                "irrelevant under the own-occupation definition.",
            },
            "exclusions": {
                "any_apply": False,
                "applicable_exclusions": [],
                "analysis": (
                    "Pre-existing condition exclusion: The Aug 14, 2022 medical note "
                    "falls AFTER the policy effective date (June 1, 2022) so it is "
                    "not within the lookback window (June 1, 2021 – May 31, 2022). "
                    "Furthermore, even if it were in the window, no treatment or "
                    "diagnosis was made — only a patient-reported symptom that was "
                    "not treated. The 12-month exclusion period (June 2022 – May 2023) "
                    "has also expired; disability onset was September 2023."
                ),
            },
            "payout": {
                "pre_disability_income": 16250.00,
                "current_income": 4000.00,
                "income_as_pct_of_predisability": 24.6,
                "disability_classification": "Total (earning < 40% of pre-disability income)",
                "monthly_benefit": 6500.00,
                "elimination_period_end": "December 14, 2023",
                "correct_payout": 6500.00,
                "calculation": (
                    "Dr. Vasquez earns $4,000 / $16,250 = 24.6% of pre-disability income. "
                    "Under Section 2, earning < 40% = Totally Disabled → full monthly "
                    "benefit of $6,500 is payable. Elimination period ended Dec 14, 2023. "
                    "Benefits commence Dec 14, 2023."
                ),
            },
            "fraud_flags": [
                {
                    "indicator": "continued_partial_work",
                    "description": "Dr. Vasquez continues working in a reduced capacity "
                    "($4,000/month). This is not fraud — it is expected and addressed "
                    "by Section 2 (partial disability). Earning < 40% qualifies for "
                    "full benefit.",
                    "severity": "low",
                },
            ],
            "correct_decision": "approve",
            "correct_decision_amount": 6500.00,
            "decision_reasoning": (
                "Approve $6,500/month beginning December 14, 2023. Own-occupation "
                "definition applies (within first 24 months). Surgery is a material "
                "duty of an orthopedic surgeon. Pre-existing exclusion does not apply "
                "(lookback window pre-dates any relevant note; exclusion period expired "
                "May 2023; disability onset September 2023). Earning < 40% of "
                "pre-disability income = total disability under Section 2."
            ),
        },
        "scoring_weights": {
            "eligibility": 0.10,
            "coverage": 0.20,
            "exclusions": 0.20,
            "payout": 0.20,
            "fraud": 0.10,
            "decision": 0.20,
        },
    }


TASKS = {
    "easy_auto_collision": _task_easy,
    "medium_medical_exclusions": _task_medium,
    "hard_property_fraud": _task_hard,
    "easy_travel_cancellation": _task_travel,
    "medium_pet_surgery": _task_pet,
    "medium_life_benefit": _task_life,
    "medium_liability_injury": _task_liability,
    "hard_flood_exclusion": _task_flood,
    "hard_disability_claim": _task_disability,
}


def get_task(task_id: str) -> Dict[str, Any]:
    """Get a task by ID. Raises KeyError if not found."""
    if task_id not in TASKS:
        available = list(TASKS.keys())
        raise KeyError(f"Task '{task_id}' not found. Available: {available}")
    return TASKS[task_id]()
