import json
import os
from datetime import datetime
from typing import List, Dict, Any

LEADS_FILE = "/home/coden809/CHATTY/leads.json"

def save_lead(lead_data: Dict[str, Any]):
    """Save a lead to the JSON storage (dedupe by email)."""
    leads = get_all_leads()
    email = (lead_data.get("email") or "").strip().lower()

    for lead in leads:
        if email and lead.get("email", "").strip().lower() == email:
            lead["updated_at"] = datetime.now().isoformat()
            lead["lead_score"] = max(lead.get("lead_score", 0), lead_data.get("lead_score", 0))
            metadata = lead.get("metadata", {})
            metadata.update(lead_data.get("metadata", {}))
            lead["metadata"] = metadata
            if "status" in lead_data:
                lead["status"] = lead_data["status"]
            if "source" in lead_data:
                lead["source"] = lead_data["source"]
            if "follow_up" in lead_data:
                lead["follow_up"] = lead_data["follow_up"]
            else:
                lead.setdefault("follow_up", {"attempts": 0, "last_sent": None, "next_run": None})
            with open(LEADS_FILE, "w") as f:
                json.dump(leads, f, indent=4)
            return lead

    lead_id = len(leads) + 1
    lead_data["id"] = lead_id
    lead_data["created_at"] = datetime.now().isoformat()
    if "status" not in lead_data:
        lead_data["status"] = "new"
    if "follow_up" not in lead_data:
        lead_data["follow_up"] = {"attempts": 0, "last_sent": None, "next_run": None}

    leads.append(lead_data)

    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)

    return lead_data

def get_all_leads() -> List[Dict[str, Any]]:
    """Get all leads from storage"""
    if not os.path.exists(LEADS_FILE):
        return []
    
    try:
        with open(LEADS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def update_lead_status(lead_id: int, status: str):
    """Update a lead's status"""
    leads = get_all_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["status"] = status
            lead["updated_at"] = datetime.now().isoformat()
            break
    
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)

def update_lead_follow_up(lead_id: int, follow_up_payload: Dict[str, Any]):
    """Update a lead's follow-up metadata"""
    leads = get_all_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["follow_up"] = follow_up_payload
            lead["updated_at"] = datetime.now().isoformat()
            break
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)


def add_lead(name: str, email: str, source: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper for API: add lead with minimal info."""
    lead_data = {
        "name": name,
        "email": email,
        "source": source,
        "lead_score": 80,
        "metadata": metadata or {}
    }
    return save_lead(lead_data)

if __name__ == "__main__":
    # Test
    test_lead = {
        "name": "Public Health Director",
        "email": "director@broomecountypublichealth.gov",
        "company": "Broome County Department of Health",
        "source": "Cold Outreach",
        "lead_score": 85
    }
    print(f"Saving test lead: {save_lead(test_lead)}")
    print(f"Total leads: {len(get_all_leads())}")
