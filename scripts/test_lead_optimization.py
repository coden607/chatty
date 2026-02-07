import os
import json
import leads_storage

def test_optimization():
    # Initial state
    leads = leads_storage.get_all_leads()
    initial_count = len(leads)

    # Add a lead
    new_lead = leads_storage.add_lead("Test Lead", "test@example.com", "test_script")

    # Check if cache is updated (without re-reading from disk)
    # We can check the global variables in leads_storage
    assert leads_storage._leads_cache is not None
    assert any(l['email'] == "test@example.com" for l in leads_storage._leads_cache)

    # Check file size/format
    with open(leads_storage.LEADS_FILE, 'r') as f:
        content = f.read()
        # Should not contain newlines if indent=None
        # But wait, json.dump(leads, f) uses default separators which might include spaces but not newlines
        assert "\n" not in content

    print(f"✅ Success! Cache updated and JSON is compact. Total leads: {len(leads_storage._leads_cache)}")

if __name__ == "__main__":
    test_optimization()
