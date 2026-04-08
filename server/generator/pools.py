"""
Randomization pools for procedural scenario generation.

All templates, names, amounts, exclusions, fraud indicators, etc.
used by the generators to create unique scenarios.
"""

from typing import Any, Dict, List

# ─── Names ───────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Sarah", "David", "Maria", "Robert", "Jennifer", "Michael", "Lisa",
    "James", "Emily", "Daniel", "Rachel", "Thomas", "Amanda", "Kevin",
    "Sophia", "Andrew", "Olivia", "Brian", "Natalie", "Christopher",
    "Hannah", "Mark", "Jessica", "Steven", "Lauren", "Patrick", "Megan",
    "Timothy", "Ashley", "Gregory", "Samantha", "Eric", "Nicole", "Ryan",
]

LAST_NAMES = [
    "Mitchell", "Chen", "Gonzalez", "Jameson", "Williams", "Patel",
    "O'Brien", "Kim", "Rodriguez", "Thompson", "Martinez", "Anderson",
    "Jackson", "White", "Harris", "Clark", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Hill",
    "Adams", "Nelson", "Baker", "Carter", "Moore", "Taylor", "Lee",
]

STREETS = [
    "Main St", "Oak Ave", "Elm St", "Pine Rd", "Maple Dr", "Cedar Ln",
    "Washington Blvd", "Park Ave", "Lake Dr", "River Rd", "Hill St",
    "Sunset Blvd", "Broadway", "Cherry Ln", "Walnut St", "Spring Rd",
]

CITIES = [
    "Westborough, MA", "Springfield, IL", "Portland, OR", "Austin, TX",
    "Denver, CO", "Seattle, WA", "Nashville, TN", "Charlotte, NC",
    "Minneapolis, MN", "Phoenix, AZ", "San Diego, CA", "Columbus, OH",
    "Raleigh, NC", "Tampa, FL", "Salt Lake City, UT", "Omaha, NE",
]

HOSPITALS = [
    "Springfield General Hospital", "St. Mary's Medical Center",
    "Community Health Hospital", "Riverside Medical Center",
    "Metro General Hospital", "University Medical Center",
    "Mercy Hospital", "Good Samaritan Hospital",
]

AUTO_SHOPS = [
    "Mike's Auto Body", "Precision Collision Repair", "A1 Auto Works",
    "Eagle Auto Body", "City Collision Center", "Premier Auto Repair",
]

CONTRACTORS = [
    "ABC Construction", "Premier Home Repair", "Quality Builders",
    "Reliable Restoration", "First Choice Construction",
]

# ─── Insurance Types ─────────────────────────────────────────────────

INSURANCE_TYPES = ["auto", "medical", "home", "travel"]

# ─── Auto Insurance ──────────────────────────────────────────────────

AUTO_SECTIONS = {
    "collision": {
        "description": "Covers damage when the insured vehicle collides with another vehicle or object, regardless of fault.",
        "deductible_range": (250, 2000),
        "limit_range": (15000, 50000),
        "rate_range": (0.75, 1.0),
    },
    "comprehensive": {
        "description": "Covers non-collision damage including theft, vandalism, natural disasters, and animal strikes.",
        "deductible_range": (100, 1000),
        "limit_range": (15000, 50000),
        "rate_range": (0.80, 1.0),
    },
    "liability": {
        "description": "Covers bodily injury and property damage to third parties caused by the policyholder.",
        "deductible_range": (0, 500),
        "limit_range": (25000, 100000),
        "rate_range": (0.85, 1.0),
    },
}

AUTO_EXCLUSIONS = [
    {"id": "commercial_use", "text": "Damage while vehicle is used for commercial purposes (rideshare, delivery)"},
    {"id": "international", "text": "Damage occurring outside the United States"},
    {"id": "racing", "text": "Damage during racing, speed contests, or off-road events"},
    {"id": "wear_and_tear", "text": "Normal wear and tear or mechanical breakdown"},
    {"id": "intentional", "text": "Intentional damage by the policyholder"},
    {"id": "uninsured_storage", "text": "Damage while vehicle is in long-term uninsured storage"},
    {"id": "unauthorized_driver", "text": "Damage caused by an unauthorized or unlicensed driver"},
]

AUTO_CONDITIONS = [
    "Claims must be reported within {deadline_days} days of the incident",
    "Police report required for claims exceeding ${police_threshold:,}",
    "The policyholder must cooperate with any investigation",
    "Vehicle must be available for inspection upon request",
]

AUTO_CLAIM_ITEMS = [
    {"name": "front_bumper", "label": "Front bumper replacement", "range": (800, 3500)},
    {"name": "rear_bumper", "label": "Rear bumper replacement", "range": (700, 3000)},
    {"name": "hood_repair", "label": "Hood repair/replacement", "range": (1000, 4000)},
    {"name": "headlight", "label": "Headlight assembly replacement", "range": (500, 2500)},
    {"name": "taillight", "label": "Taillight assembly replacement", "range": (300, 1500)},
    {"name": "windshield", "label": "Windshield replacement", "range": (300, 1200)},
    {"name": "door_repair", "label": "Door panel repair", "range": (800, 3000)},
    {"name": "paint_work", "label": "Paint and refinishing", "range": (500, 3000)},
    {"name": "frame_repair", "label": "Frame/structural repair", "range": (2000, 8000)},
    {"name": "radiator", "label": "Radiator replacement", "range": (500, 2000)},
    {"name": "airbag", "label": "Airbag replacement", "range": (1000, 3000)},
    {"name": "suspension", "label": "Suspension repair", "range": (800, 3500)},
    {"name": "towing", "label": "Towing charges", "range": (100, 500)},
    {"name": "rental_car", "label": "Rental car (during repairs)", "range": (300, 1500)},
]

AUTO_SCENARIOS = [
    "rear-end collision at a traffic light",
    "side-impact collision at an intersection",
    "single-vehicle accident (hit a guardrail)",
    "parking lot collision with another vehicle",
    "multi-vehicle pileup on the highway",
    "hit a deer while driving at night",
    "vehicle struck by fallen tree branch during storm",
    "vandalism in apartment complex parking lot",
]

# ─── Medical Insurance ───────────────────────────────────────────────

MEDICAL_SECTIONS = {
    "inpatient": {
        "description": "Covers medically necessary inpatient hospital stays.",
        "sub_items": {
            "room_board": {"label": "Room and board (semi-private)", "rate_range": (0.80, 1.0)},
            "surgeon": {"label": "Surgeon fees", "rate_range": (0.70, 0.90)},
            "anesthesia": {"label": "Anesthesia", "rate_range": (0.70, 0.90)},
            "lab_work": {"label": "Lab work and diagnostics", "rate_range": (0.90, 1.0)},
        },
        "deductible_range": (500, 3000),
        "limit_range": (50000, 500000),
    },
    "outpatient": {
        "description": "Covers outpatient services and procedures.",
        "sub_items": {
            "office_visit": {"label": "Office visits", "copay_range": (20, 60)},
            "imaging": {"label": "Diagnostic imaging (X-ray, MRI, CT)", "rate_range": (0.60, 0.80)},
            "physical_therapy": {"label": "Physical therapy", "rate_range": (0.50, 0.70), "session_limit": (12, 30)},
        },
        "deductible_range": (250, 1500),
    },
    "prescription": {
        "description": "Covers prescription medications.",
        "sub_items": {
            "generic": {"label": "Generic drugs", "copay_range": (5, 20)},
            "brand_formulary": {"label": "Brand-name (formulary)", "copay_range": (30, 60)},
            "brand_non_formulary": {"label": "Brand-name (non-formulary)", "rate_range": (0.40, 0.60)},
            "specialty": {"label": "Specialty drugs", "rate_range": (0.25, 0.40)},
        },
    },
}

MEDICAL_EXCLUSIONS = [
    {"id": "cosmetic", "text": "Cosmetic procedures unless medically necessary due to accident or illness"},
    {"id": "experimental", "text": "Experimental or investigational treatments not approved by the FDA"},
    {"id": "out_of_network", "text": "Services received outside the provider network without prior authorization"},
    {"id": "pre_existing", "text": "Pre-existing conditions during the first {waiting_months} months of coverage"},
    {"id": "dental", "text": "Dental services (separate dental plan required)"},
    {"id": "vision", "text": "Vision correction surgery (LASIK, PRK)"},
    {"id": "weight_loss", "text": "Weight loss surgery unless BMI exceeds 40"},
    {"id": "alternative_medicine", "text": "Alternative medicine (acupuncture, homeopathy) unless pre-approved"},
]

MEDICAL_CLAIM_ITEMS = [
    {"name": "er_visit", "label": "Emergency room visit", "section": "inpatient", "range": (2000, 8000)},
    {"name": "surgery", "label": "Surgical procedure", "section": "inpatient", "range": (5000, 30000)},
    {"name": "anesthesia", "label": "Anesthesia", "section": "inpatient", "range": (1500, 6000)},
    {"name": "room_board", "label": "Hospital room", "section": "inpatient", "range": (4000, 20000)},
    {"name": "lab_work", "label": "Lab work and blood tests", "section": "inpatient", "range": (500, 3000)},
    {"name": "mri_scan", "label": "MRI scan", "section": "outpatient", "range": (1500, 5000)},
    {"name": "xray", "label": "X-ray imaging", "section": "outpatient", "range": (200, 800)},
    {"name": "physical_therapy", "label": "Physical therapy sessions", "section": "outpatient", "range": (1200, 4000)},
    {"name": "generic_rx", "label": "Generic prescription", "section": "prescription", "range": (15, 80)},
    {"name": "brand_rx", "label": "Brand-name prescription", "section": "prescription", "range": (100, 400)},
    {"name": "dental_work", "label": "Dental procedure", "section": "excluded_dental", "range": (500, 3000)},
    {"name": "cosmetic", "label": "Cosmetic procedure", "section": "excluded_cosmetic", "range": (2000, 10000)},
]

MEDICAL_SCENARIOS = [
    "emergency appendectomy",
    "broken arm from a fall",
    "knee replacement surgery",
    "gallbladder removal",
    "emergency cardiac care",
    "back surgery (herniated disc)",
    "ACL reconstruction",
    "pneumonia requiring hospitalization",
]

# ─── Home Insurance ──────────────────────────────────────────────────

HOME_SECTIONS = {
    "dwelling": {
        "description": "Covers damage to the insured dwelling from covered perils.",
        "perils": ["fire", "lightning", "windstorm", "hail", "explosion", "smoke", "vandalism", "theft"],
        "deductible_range": (1000, 5000),
        "limit_range": (150000, 500000),
        "rate_range": (0.90, 1.0),
    },
    "personal_property": {
        "description": "Covers personal belongings inside the dwelling.",
        "deductible_range": (500, 2500),
        "limit_range": (50000, 200000),
        "rate_range": (0.80, 1.0),
        "high_value_cap": 2500,
    },
    "additional_living": {
        "description": "Covers additional living expenses if dwelling is uninhabitable.",
        "limit_range": (30000, 100000),
    },
}

HOME_EXCLUSIONS = [
    {"id": "flood", "text": "Flood damage (separate flood policy required)"},
    {"id": "earthquake", "text": "Earthquake damage"},
    {"id": "mold", "text": "Gradual deterioration, rust, mold (unless caused by covered peril)"},
    {"id": "intentional", "text": "Intentional acts by the policyholder or household members"},
    {"id": "vacancy", "text": "If dwelling is vacant for more than {vacancy_days} consecutive days, vandalism and theft coverage is suspended"},
    {"id": "business_property", "text": "Business property and equipment used for commercial purposes"},
    {"id": "pets", "text": "Damage from pets owned by the policyholder"},
    {"id": "ordinance", "text": "Cost to bring property up to current building codes (ordinance or law)"},
]

HOME_CLAIM_ITEMS_DWELLING = [
    {"name": "roof_repair", "label": "Roof repair/replacement", "range": (3000, 25000)},
    {"name": "door_replacement", "label": "Door replacement and frame repair", "range": (1000, 5000)},
    {"name": "window_replacement", "label": "Window replacement", "range": (500, 4000)},
    {"name": "fire_damage", "label": "Fire damage and smoke remediation", "range": (5000, 50000)},
    {"name": "wall_repair", "label": "Interior wall repairs and repainting", "range": (2000, 15000)},
    {"name": "flooring", "label": "Flooring replacement", "range": (3000, 20000)},
    {"name": "plumbing", "label": "Plumbing repair", "range": (1000, 8000)},
    {"name": "electrical", "label": "Electrical repair", "range": (1000, 6000)},
]

HOME_CLAIM_ITEMS_PERSONAL = [
    {"name": "tv", "label": "Television", "range": (500, 3500), "high_value": False},
    {"name": "laptop", "label": "Laptop computer", "range": (800, 4500), "high_value": False},
    {"name": "jewelry", "label": "Jewelry", "range": (2000, 15000), "high_value": True},
    {"name": "watch", "label": "Watch", "range": (1000, 12000), "high_value": True},
    {"name": "art", "label": "Artwork", "range": (1000, 20000), "high_value": True},
    {"name": "electronics", "label": "Electronics and gadgets", "range": (500, 3000), "high_value": False},
    {"name": "clothing", "label": "Designer clothing and shoes", "range": (1000, 8000), "high_value": False},
    {"name": "furniture", "label": "Furniture", "range": (1000, 10000), "high_value": False},
    {"name": "instruments", "label": "Musical instruments", "range": (500, 15000), "high_value": True},
    {"name": "cash", "label": "Cash", "range": (500, 5000), "high_value": True},
    {"name": "gaming", "label": "Gaming console and games", "range": (400, 1500), "high_value": False},
]

HOME_SCENARIOS = [
    "break-in and theft while away on vacation",
    "kitchen fire caused by electrical fault",
    "windstorm damaged the roof and caused water intrusion",
    "vandalism while property was being renovated",
    "tree fell on the house during a storm",
    "pipe burst caused flooding in the basement",
]

# ─── Travel Insurance ────────────────────────────────────────────────

TRAVEL_SECTIONS = {
    "trip_cancellation": {
        "description": "Covers non-refundable trip costs if trip is cancelled for a covered reason.",
        "covered_reasons": ["illness or injury", "death of family member", "airline cancellation",
                           "natural disaster at destination", "jury duty", "job loss"],
        "deductible_range": (0, 500),
        "limit_range": (5000, 25000),
        "rate_range": (0.80, 1.0),
    },
    "medical_emergency": {
        "description": "Covers emergency medical treatment while traveling.",
        "deductible_range": (100, 500),
        "limit_range": (25000, 100000),
        "rate_range": (0.80, 1.0),
    },
    "baggage": {
        "description": "Covers lost, stolen, or damaged baggage.",
        "deductible_range": (50, 250),
        "limit_range": (1000, 5000),
        "rate_range": (0.80, 1.0),
        "per_item_cap": 500,
    },
}

TRAVEL_EXCLUSIONS = [
    {"id": "pre_existing_travel", "text": "Pre-existing medical conditions not disclosed at purchase"},
    {"id": "high_risk", "text": "Injuries from high-risk activities (skydiving, bungee jumping, scuba below 40m)"},
    {"id": "government_advisory", "text": "Travel to destinations under government travel advisory"},
    {"id": "alcohol", "text": "Incidents where alcohol or illegal drugs were a contributing factor"},
    {"id": "change_of_mind", "text": "Cancellation due to change of mind or schedule preference"},
    {"id": "carrier_default", "text": "Financial default of the travel supplier (airline bankruptcy)"},
]

TRAVEL_SCENARIOS = [
    "flight cancelled due to severe weather",
    "medical emergency while on vacation abroad",
    "luggage lost by airline during connection",
    "trip cancelled due to sudden illness before departure",
    "hotel evacuation due to natural disaster",
]

# ─── Fraud Indicators ────────────────────────────────────────────────

FRAUD_INDICATORS = [
    {
        "type": "timing",
        "description_template": "Only {days} days between policy inception ({inception}) and claim date ({claim_date}). Extremely suspicious timing.",
        "severity": "high",
    },
    {
        "type": "inflated_values",
        "description_template": "Claimed amount for {item} is ${claimed:,.2f} but receipt shows actual purchase price of ${actual:,.2f}. Systematic inflation of {pct:.0f}%.",
        "severity": "high",
    },
    {
        "type": "related_contractor",
        "description_template": "Repair estimate from '{contractor}' — shares surname with policyholder ({holder_name}). Potential conflict of interest.",
        "severity": "medium",
    },
    {
        "type": "prior_claims",
        "description_template": "Policyholder has {count} prior {claim_type} claims with different insurers in the past {years} years. Pattern of similar claims across carriers.",
        "severity": "high",
    },
    {
        "type": "items_moved",
        "description_template": "Neighbor observed policyholder loading {items} into a {vehicle} {days_before} days before the reported incident.",
        "severity": "high",
    },
    {
        "type": "suspicious_fire",
        "description_template": "Fire department notes '{finding}'. Burn pattern is inconsistent with reported cause.",
        "severity": "medium",
    },
    {
        "type": "no_receipts",
        "description_template": "No receipts or proof of purchase for {count} high-value items totaling ${total:,.2f} in claims. Required by policy Section {section} for items over ${threshold:,}.",
        "severity": "medium",
    },
    {
        "type": "no_security",
        "description_template": "No {security_type} was active on a newly insured property with ${value:,.2f} in claimed valuables.",
        "severity": "low",
    },
    {
        "type": "inconsistent_story",
        "description_template": "Claimant's account states '{claim_detail}' but {evidence_source} shows '{evidence_detail}'. Inconsistent timeline.",
        "severity": "high",
    },
    {
        "type": "witness_contradiction",
        "description_template": "Witness {witness_name} states: '{witness_statement}'. This contradicts the claimant's account of events.",
        "severity": "medium",
    },
    {
        "type": "financial_distress",
        "description_template": "Public records show {financial_detail}. Financial motive for fraudulent claim.",
        "severity": "medium",
    },
    {
        "type": "duplicate_claim",
        "description_template": "Similar claim for {item} was filed with {other_insurer} on {other_date}. Potential double-dipping.",
        "severity": "high",
    },
]
