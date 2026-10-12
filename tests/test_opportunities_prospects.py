"""Offline tests for the Cortese prospect finder, budget guard, drafts and digest."""

import inspect

import pytest

from opportunities import digest
from opportunities.config import Settings
from opportunities.models import Job, Prospect
from opportunities.prospects import drafts, finder, places
from opportunities.prospects.export import to_csv
from opportunities.prospects.metros import METROS
from opportunities.prospects.scoring import hours_signals, score_prospect
from opportunities.prospects.website import analyze_html
from opportunities.store import Store


@pytest.fixture
def settings(tmp_path, monkeypatch):
    for k in ("GOOGLE_PLACES_API_KEY", "RESEND_API_KEY", "OPP_DIGEST_TO", "OPP_DIGEST_FROM", "RESEND_FROM_EMAIL", "OPENROUTER_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("OPP_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("OPP_OUTPUT_DIR", str(tmp_path / "out"))
    return Settings()


def test_top_100_metros():
    assert len(METROS) == 100 and len({m[0] for m in METROS}) == 100


def test_hours_signals():
    hrs = ["Monday: 8:00 AM – 5:00 PM", "Tuesday: 8:00 AM – 5:00 PM", "Wednesday: 8:00 AM – 5:00 PM",
           "Thursday: 8:00 AM – 5:00 PM", "Friday: 8:00 AM – 2:00 PM", "Saturday: Closed", "Sunday: Closed"]
    s = hours_signals(hrs)
    assert s == {"closed_weekends": True, "closes_by_6pm": True}
    assert hours_signals(["Monday: Open 24 hours"]) == {"open_24h": True}


def test_website_signal_detection():
    assert analyze_html("<a href='https://www.zocdoc.com/x'>Book online</a>")["online_booking"] is True
    s = analyze_html("<html><a href='tel:5551234'>Call us</a></html>")
    assert s["online_booking"] is False and s["chat_or_text_widget"] is False and s["tel_links"] == 1
    assert analyze_html("<script src='https://widget.podium.com/x.js'></script>")["chat_or_text_widget"] is True


def test_grading_a_vs_c():
    hot = Prospect(source="Google Places", source_id="p1", name="Smile Dental", vertical="dental", metro="Austin",
                   phone="(512) 555-0100", website="https://smile.example", rating=4.7, review_count=120,
                   hours=["Monday: 8:00 AM – 5:00 PM", "Saturday: Closed", "Sunday: Closed"],
                   signals={"website_checked": True, "online_booking": False, "chat_or_text_widget": False, "after_hours_mention": False})
    g, s, r = score_prospect(hot)
    assert g == "A" and s >= 65 and "no online booking on site" in r
    cold = Prospect(source="Google Places", source_id="p2", name="Big Chain", vertical="auto_repair", metro="Austin", phone="")
    assert score_prospect(cold)[0] == "C"


def test_places_skipped_without_key(settings):
    r = finder.discover_places(settings, Store(":memory:"), METROS[:2], 10)
    assert r["skipped"] == "missing GOOGLE_PLACES_API_KEY" and r["prospects"] == []


def test_places_budget_guard(settings, monkeypatch):
    monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test")
    monkeypatch.setenv("OPP_PLACES_MONTHLY_BUDGET_USD", "0.07")
    monkeypatch.setenv("OPP_PLACES_COST_PER_CALL_USD", "0.035")
    s = Settings()
    assert s.places_monthly_call_cap == 2
    calls = []

    class Resp:
        status_code = 200
        text = ""
        def json(self):
            return {"places": [{"id": f"id{len(calls)}", "displayName": {"text": "Biz"}, "nationalPhoneNumber": f"(512) 555-01{len(calls):02d}", "businessStatus": "OPERATIONAL"}]}

    def fake_request(*a, **k):
        calls.append(k.get("json"))
        return Resp()

    monkeypatch.setattr(places, "request", fake_request)
    store = Store(":memory:")
    r = finder.discover_places(s, store, METROS[:3], max_calls=50)
    assert len(calls) == 2  # never exceeds the monthly cap
    assert "budget" in (r["stopped"] or "")
    assert store.usage(places.SERVICE) == 2
    assert calls[0]["textQuery"].endswith("New York, NY")


def test_places_content_purged_after_cache_window(settings):
    store = Store(":memory:")
    p = Prospect(source="Google Places", source_id="pid", name="Old Biz", vertical="dental", metro="X", phone="1", fetched_at="2020-01-01T00:00:00+00:00")
    store.upsert_prospects([p])
    assert store.purge_stale_places_content(30) == 1
    row = store.list_prospects()[0]
    assert row["source_id"] == "pid" and row["phone"] == "" and row["name"].startswith("[expired")


def test_drafts_are_never_sent(settings, tmp_path):
    p = Prospect(source="Google Places", source_id="p1", name="Smile Dental", vertical="dental", metro="Austin", city="Austin", state="TX",
                 phone="(512) 555-0100", website="https://smile.example", grade="A", score=80,
                 signals={"website_checked": True, "online_booking": False, "chat_or_text_widget": False}).to_dict()
    subject, body, gen = drafts.draft_for(p, settings)
    assert gen == "template" and "Smile Dental" in subject
    assert "reply \"no thanks\"" in body and settings.sender_company in body  # CAN-SPAM opt-out + identity
    path = drafts.write_draft_file(tmp_path, p, subject, body, gen)
    assert "DRAFT ONLY" in path.read_text()
    src = inspect.getsource(drafts) + inspect.getsource(finder)
    for forbidden in ("api.resend.com", "sendgrid", "smtplib", "twilio", "send_email", "send_message"):
        assert forbidden not in src.lower()


def test_csv_export(settings):
    out = to_csv([{"grade": "A", "score": 80, "name": "Smile Dental", "reasons": ["x", "y"]}])
    assert out.splitlines()[0].startswith("grade,score,name") and "x; y" in out


def test_find_prospects_offline_persists_and_drafts(settings, monkeypatch):
    monkeypatch.setattr(finder.npi, "search", lambda tax, v, m, c, s, st: [
        Prospect(source="NPI Registry", source_id="123", name="Smile Dental", vertical=v, metro=m, phone="(512) 555-0100", city=c, state=s)])
    store = Store(settings.db_path)
    r = finder.find_prospects(settings, store=store, metro_limit=1, use_places=True, check_websites=False, draft_grades="ABC")
    assert r["summary"]["google_places"]["skipped"]
    assert r["summary"]["unique"] >= 1
    assert r["summary"]["drafts_saved"] >= 1
    assert all(d["status"] == "draft" for d in store.list_drafts())


def test_digest_only_to_configured_address_and_saved_without_key(settings):
    j = Job(source="Remotive", source_url="https://remotive.com/x", title="Python Engineer", company="A", url="https://remotive.com/x", score=80).to_dict()
    d = digest.build([j])
    assert "via Remotive" in d["text"] and "https://remotive.com/x" in d["html"]
    res = digest.send_or_save(d, settings)
    assert res["sent"] is False and "RESEND_API_KEY" in res["missing"]


def test_digest_rejects_multiple_recipients(settings, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    monkeypatch.setenv("OPP_DIGEST_FROM", "bot@example.com")
    monkeypatch.setenv("OPP_DIGEST_TO", "a@example.com, b@example.com")
    s = Settings()
    called = []
    monkeypatch.setattr(digest.httpx, "post", lambda *a, **k: called.append(1))
    res = digest.send_or_save({"subject": "s", "text": "t", "html": "h"}, s)
    assert res["sent"] is False and not called
