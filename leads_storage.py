import json
import os
from datetime import datetime
from typing import List, Dict, Any

# Resolve LEADS_FILE dynamically relative to the script location
LEADS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.json")

# In-memory cache for leads to minimize disk I/O and JSON parsing overhead
_leads_cache = None
_last_mtime = 0

def _update_cache(leads):
    """Helper to update the in-memory cache and mtime"""
    global _leads_cache, _last_mtime
    _leads_cache = leads
    try:
        if os.path.exists(LEADS_FILE):
            _last_mtime = os.path.getmtime(LEADS_FILE)
        else:
            _last_mtime = 0
    except (OSError, FileNotFoundError):
        _last_mtime = 0

def save_lead(lead_data: Dict[str, Any]):
    """Save a lead to the JSON storage (dedupe by email)."""
    leads = get_all_leads()
    email = (lead_data.get("email") or "").strip().lower()

    target_lead = None
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
            target_lead = lead
            break

    if target_lead is None:
        lead_id = len(leads) + 1
        lead_data["id"] = lead_id
        lead_data["created_at"] = datetime.now().isoformat()
        if "status" not in lead_data:
            lead_data["status"] = "new"
        if "follow_up" not in lead_data:
            lead_data["follow_up"] = {"attempts": 0, "last_sent": None, "next_run": None}
        leads.append(lead_data)
        target_lead = lead_data

    with open(LEADS_FILE, "w") as f:
        json.dump(leads, f, indent=4)

    _update_cache(leads)
    return target_lead

def get_all_leads() -> List[Dict[str, Any]]:
    """Get all leads from storage (with in-memory caching)"""
    global _leads_cache, _last_mtime

    if not os.path.exists(LEADS_FILE):
        return []
    
    try:
        # Check if file has been modified since last load
        current_mtime = os.path.getmtime(LEADS_FILE)
        if _leads_cache is not None and current_mtime <= _last_mtime:
            return _leads_cache

        with open(LEADS_FILE, "r") as f:
            _leads_cache = json.load(f)
            _last_mtime = current_mtime
            return _leads_cache
    except Exception:
        # Return empty list or cached version if read fails
        return _leads_cache if _leads_cache is not None else []

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

    _update_cache(leads)

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

    _update_cache(leads)


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
