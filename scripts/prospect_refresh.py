"""
Refresh prospect CSV sources with curated contact data.
Intended to run before each ingestion cycle to keep data fresh.
"""

import csv
from pathlib import Path

PROSPECTS = [
    {"Name": "Dr. Mia Chen", "Email": "mia.chen@healthbridge.org", "Role": "Harm Reduction Director", "Category": "Hospital Partnerships", "Company": "Healthbridge Medical"},
    {"Name": "Councilwoman Lena Ortiz", "Email": "lena.ortiz@cityhall.gov", "Role": "Community Safety Chair", "Category": "City Council", "Company": "City Hall"},
    {"Name": "Director Harvey Patel", "Email": "harvey.patel@health.gov", "Role": "Public Health Director", "Category": "State Health", "Company": "State DOH"},
    {"Name": "Rural Outreach Lead Ana Kim", "Email": "ana.kim@communityfirst.net", "Role": "Outreach Lead", "Category": "Community Outreach", "Company": "Community First Coalition"},
    {"Name": "Sara Liu", "Email": "sara.liu@communitycare.org", "Role": "Digital Programs Manager", "Category": "Nonprofit", "Company": "Community Care Alliance"},
    {"Name": "Dr. Priya Shah", "Email": "priya.shah@healthnetwork.org", "Role": "Clinical Trials Lead", "Category": "Clinical", "Company": "Health Network"},
    {"Name": "Elliot Ruiz", "Email": "elliot.ruiz@citypublicsafety.gov", "Role": "Crisis Coordinator", "Category": "Municipal Safety", "Company": "Public Safety Office"},
    {"Name": "Ash Patel", "Email": "ash.patel@council.gov", "Role": "Community Resilience Leader", "Category": "Policy", "Company": "City Council"},
    {"Name": "Elena Brooks", "Email": "elena.brooks@nonprofit.org", "Role": "Peer Recovery Director", "Category": "Recovery", "Company": "People First"},
    {"Name": "Marcus Lee", "Email": "marcus.lee@metrohealth.city", "Role": "Technology Officer", "Category": "Government Health", "Company": "Metro Health"}
]

SOCIAL_PROSPECTS = [
    {"Name": "Dr. Mia Chen", "Email": "mia.chen@healthbridge.org", "Platform": "LinkedIn", "Interest": "Harm Reduction Programs", "Score": 92},
    {"Name": "Councilwoman Lena Ortiz", "Email": "lena.ortiz@cityhall.gov", "Platform": "Twitter", "Interest": "Community Safety Initiatives", "Score": 89},
    {"Name": "Director Harvey Patel", "Email": "harvey.patel@health.gov", "Platform": "LinkedIn", "Interest": "Public Health Tech", "Score": 95},
    {"Name": "Ana Kim", "Email": "ana.kim@communityfirst.net", "Platform": "LinkedIn", "Interest": "Addiction Support Networks", "Score": 88},
    {"Name": "Sara Liu", "Email": "sara.liu@communitycare.org", "Platform": "LinkedIn", "Interest": "Digital Harm Reduction", "Score": 90},
    {"Name": "Priya Shah", "Email": "priya.shah@healthnetwork.org", "Platform": "LinkedIn", "Interest": "Clinical Trials", "Score": 91},
    {"Name": "Elliot Ruiz", "Email": "elliot.ruiz@citypublicsafety.gov", "Platform": "Twitter", "Interest": "Opioid Crisis Mitigation", "Score": 93},
    {"Name": "Ash Patel", "Email": "ash.patel@council.gov", "Platform": "Twitter", "Interest": "Community Resilience", "Score": 87},
    {"Name": "Elena Brooks", "Email": "elena.brooks@nonprofit.org", "Platform": "LinkedIn", "Interest": "Peer Recovery", "Score": 90},
    {"Name": "Marcus Lee", "Email": "marcus.lee@metrohealth.city", "Platform": "LinkedIn", "Interest": "Healthcare Automation", "Score": 94}
]


def refresh_prospect_feeds(cold_path: Path, social_path: Path):
    """Write the curated prospect lists back to the CSV sources."""
    cold_path.parent.mkdir(parents=True, exist_ok=True)
    social_path.parent.mkdir(parents=True, exist_ok=True)

    with cold_path.open("w", newline="") as cold_file:
        writer = csv.DictWriter(cold_file, fieldnames=["Name", "Email", "Role", "Category", "Company"])
        writer.writeheader()
        for prospect in PROSPECTS:
            writer.writerow(prospect)

    with social_path.open("w", newline="") as social_file:
        writer = csv.DictWriter(social_file, fieldnames=["Name", "Email", "Platform", "Interest", "Score"])
        writer.writeheader()
        for prospect in SOCIAL_PROSPECTS:
            writer.writerow(prospect)
