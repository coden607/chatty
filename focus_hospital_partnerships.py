
import asyncio
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Any

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from leads_storage import save_lead, get_all_leads

def add_hospital_execs():
    """Add high-value Broome County hospital administrators to the leads database."""
    print("🏥 Identifying Broome County Hospital Decision Makers...")
    
    hospital_leads = [
        {
            "name": "John Carrigg",
            "email": "john.carrigg@nyuhs.org",
            "role": "President & CEO",
            "company": "UHS (United Health Services)",
            "source": "Institutional Research",
            "lead_score": 100,
            "metadata": {
                "geo": "Binghamton, NY",
                "department": "Executive Administration",
                "qualification_reasons": ["Hospital CEO", "Broome County influence", "Vulnerable population focus"],
                "prospect_tier": "A",
                "real_data": True
            },
            "status": "priority_outreach"
        },
        {
            "name": "Kathryn Connerton",
            "email": "kathryn.connerton@guthrie.org",
            "role": "President & CEO",
            "company": "Guthrie Lourdes Hospital",
            "source": "Institutional Research",
            "lead_score": 100,
            "metadata": {
                "geo": "Binghamton, NY",
                "department": "Executive Administration",
                "qualification_reasons": ["Hospital CEO", "Major healthcare provider", "Harm reduction potential"],
                "prospect_tier": "A",
                "real_data": True
            },
            "status": "priority_outreach"
        },
        {
            "name": "Kay Boland",
            "email": "kay.boland@nyuhs.org",
            "role": "SVP, Chief Nursing Officer & COO",
            "company": "UHS Wilson Medical Center",
            "source": "Institutional Research",
            "lead_score": 95,
            "metadata": {
                "geo": "Johnson City, NY",
                "department": "Nursing / Operations",
                "qualification_reasons": ["Hospital COO", "Nursing leadership", "Operations control"],
                "prospect_tier": "A",
                "real_data": True
            },
            "status": "priority_outreach"
        }
    ]

    new_count = 0
    existing_leads = get_all_leads()
    existing_emails = {l.get("email", "").lower() for l in existing_leads}

    for lead_data in hospital_leads:
        if lead_data["email"].lower() not in existing_emails:
            save_lead(lead_data)
            print(f"✅ Added: {lead_data['name']} ({lead_data['company']})")
            new_count += 1
        else:
            print(f"ℹ️ Skipping existing lead: {lead_data['name']}")

    print(f"\n🚀 Total hospital leads added: {new_count}")

if __name__ == "__main__":
    add_hospital_execs()
