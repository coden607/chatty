"""Cortese Digital target verticals: Places text queries and NPI taxonomies."""

VERTICALS = {
    "dental": {
        "label": "Dental practice",
        "places_queries": ["dentist"],
        "npi_taxonomies": ["Dentist"],
        "weight": 10,
        "pain": "new-patient calls that hit voicemail usually book with the next dentist on the list",
    },
    "med_spa": {
        "label": "Med spa / aesthetics",
        "places_queries": ["med spa"],
        "npi_taxonomies": ["Dermatology"],
        "weight": 5,
        "pain": "consult inquiries during treatments go unanswered and rarely call back",
    },
    "home_services": {
        "label": "Home services",
        "places_queries": ["plumber", "HVAC contractor", "electrician", "roofing contractor"],
        "npi_taxonomies": [],
        "weight": 10,
        "pain": "techs on a job can't pick up, and an unanswered service call is a lost job",
    },
    "law_firm": {
        "label": "Law firm",
        "places_queries": ["personal injury lawyer", "family law attorney"],
        "npi_taxonomies": [],
        "weight": 10,
        "pain": "potential clients call several firms and usually hire the first one that answers",
    },
    "auto_repair": {
        "label": "Auto repair",
        "places_queries": ["auto repair shop"],
        "npi_taxonomies": [],
        "weight": 5,
        "pain": "calls ring out while the team is in the bays, and those customers go elsewhere",
    },
}
