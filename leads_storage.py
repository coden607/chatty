import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any

# Use a path relative to the script location to avoid hardcoded absolute paths
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")

# Performance optimization: In-memory cache with mtime validation
# Bolt ⚡: Caching avoids redundant disk I/O and JSON parsing for every call
_leads_cache = None
_last_mtime = 0

def get_all_leads() -> List[Dict[str, Any]]:
    """Get all leads from storage (with in-memory caching for performance)"""
    global _leads_cache, _last_mtime

    if not os.path.exists(LEADS_FILE):
        return []

    try:
        # Only reload if the file has changed on disk
        current_mtime = os.path.getmtime(LEADS_FILE)
        if _leads_cache is not None and current_mtime <= _last_mtime:
            return _leads_cache

        with open(LEADS_FILE, "r") as f:
            _leads_cache = json.load(f)
            _last_mtime = current_mtime
            return _leads_cache
    except Exception:
        # Fallback to empty if file is corrupt or inaccessible
        return _leads_cache if _leads_cache is not None else []

def _write_leads(leads: List[Dict[str, Any]]):
    """Internal helper to write leads and update cache"""
    global _leads_cache, _last_mtime
    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)
    _leads_cache = leads
    _last_mtime = os.path.getmtime(LEADS_FILE)

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
            _write_leads(leads)
            return lead

    lead_id = len(leads) + 1
    lead_data["id"] = lead_id
    lead_data["created_at"] = datetime.now().isoformat()
    if "status" not in lead_data:
        lead_data["status"] = "new"
    if "follow_up" not in lead_data:
        lead_data["follow_up"] = {"attempts": 0, "last_sent": None, "next_run": None}

    leads.append(lead_data)
    _write_leads(leads)

    return lead_data

def update_lead_status(lead_id: int, status: str):
    """Update a lead's status"""
    leads = get_all_leads()
    updated = False
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["status"] = status
            lead["updated_at"] = datetime.now().isoformat()
            updated = True
            break
    
    if updated:
        _write_leads(leads)

def update_lead_follow_up(lead_id: int, follow_up_payload: Dict[str, Any]):
    """Update a lead's follow-up metadata"""
    leads = get_all_leads()
    updated = False
    for lead in leads:
        if lead.get("id") == lead_id:
            lead["follow_up"] = follow_up_payload
            lead["updated_at"] = datetime.now().isoformat()
            updated = True
            break

    if updated:
        _write_leads(leads)


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
