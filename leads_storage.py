import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

BASE_DIR = Path(__file__).parent
LEADS_FILE = BASE_DIR / "leads.json"

# In-memory cache for performance optimization
_leads_cache = None
_last_mtime = 0

def save_lead(lead_data: Dict[str, Any]):
    """Save a lead to the JSON storage (dedupe by email)."""
    global _leads_cache, _last_mtime
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

            # Update cache after write
            _leads_cache = leads
            _last_mtime = os.path.getmtime(LEADS_FILE)
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

    # Update cache after write
    _leads_cache = leads
    _last_mtime = os.path.getmtime(LEADS_FILE)

    return lead_data

def get_all_leads() -> List[Dict[str, Any]]:
    """Get all leads from storage with in-memory caching and mtime validation."""
    global _leads_cache, _last_mtime

    if not os.path.exists(LEADS_FILE):
        return []
    
    try:
        # Performance optimization: only reload from disk if file has changed
        current_mtime = os.path.getmtime(LEADS_FILE)
        if _leads_cache is not None and current_mtime <= _last_mtime:
            return _leads_cache

        with open(LEADS_FILE, "r") as f:
            _leads_cache = json.load(f)
            _last_mtime = current_mtime
            return _leads_cache
    except Exception:
        return _leads_cache if _leads_cache is not None else []

def update_lead_status(lead_id: int, status: str):
    """Update a lead's status"""
    global _leads_cache, _last_mtime
    leads = get_all_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["status"] = status
            lead["updated_at"] = datetime.now().isoformat()
            break
    
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)

    # Update cache after write
    _leads_cache = leads
    _last_mtime = os.path.getmtime(LEADS_FILE)

def update_lead_follow_up(lead_id: int, follow_up_payload: Dict[str, Any]):
    """Update a lead's follow-up metadata"""
    global _leads_cache, _last_mtime
    leads = get_all_leads()
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["follow_up"] = follow_up_payload
            lead["updated_at"] = datetime.now().isoformat()
            break
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)

    # Update cache after write
    _leads_cache = leads
    _last_mtime = os.path.getmtime(LEADS_FILE)


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
