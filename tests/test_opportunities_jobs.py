"""Offline tests for the job finder (no network: sources are fed fixtures)."""

import json
from pathlib import Path

import pytest

from opportunities.config import Settings
from opportunities.jobs import finder
from opportunities.jobs.sources import hn, himalayas, remoteok, remotive, us_eligibility, parse_salary
from opportunities.jobs.scoring import score_job
from opportunities.models import Job
from opportunities.store import Store

FIX = Path(__file__).parent / "fixtures" / "opportunities"


def load(name):
    return json.loads((FIX / name).read_text())


@pytest.fixture
def settings(tmp_path, monkeypatch):
    for k in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY", "USAJOBS_API_KEY", "USAJOBS_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("OPP_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("OPP_OUTPUT_DIR", str(tmp_path / "out"))
    return Settings()


def test_us_eligibility():
    assert us_eligibility("USA") is True
    assert us_eligibility("Remote (US or Canada)") is True
    assert us_eligibility("Europe only") is False
    assert us_eligibility("Berlin, Germany") is False
    assert us_eligibility("Worldwide") is True
    assert us_eligibility("Austin, TX") is True
    assert us_eligibility("Remote") is None


def test_parse_salary():
    assert parse_salary("$140k - $170k") == (140000, 170000)
    assert parse_salary("OTE 120,000") == (120000, 120000)
    assert parse_salary("") == (None, None)


def test_remotive_parse_and_attribution(monkeypatch, settings):
    monkeypatch.setattr(remotive, "get_json", lambda *a, **k: load("remotive.json"))
    res = remotive.fetch(settings)
    assert len(res.jobs) == 2
    j = res.jobs[0]
    assert j.source == "Remotive" and j.source_url.startswith("https://remotive.com/")
    assert j.us_eligible is True and j.salary_min == 140000
    assert "Remotive" in j.attribution


def test_remoteok_skips_legal_notice(monkeypatch, settings):
    monkeypatch.setattr(remoteok, "get_json", lambda *a, **k: load("remoteok.json"))
    res = remoteok.fetch(settings)
    assert [j.company for j in res.jobs] == ["Acme AI", "SalesCo"]
    assert res.jobs[0].url.startswith("https://remoteOK.com/")  # followed link back to Remote OK


def test_himalayas_location_restrictions(monkeypatch, settings):
    monkeypatch.setattr(himalayas, "get_json", lambda *a, **k: load("himalayas.json"))
    res = himalayas.fetch(settings)
    by = {j.company: j for j in res.jobs}
    assert by["Lift"].us_eligible is True
    assert by["BerlinCo"].us_eligible is False
    assert by["BerlinCo"].salary_min is None  # non-USD salary ignored


def test_hn_parses_only_remote_headers():
    jobs = [hn.parse_comment(c) for c in load("hn_item.json")["children"]]
    jobs = [j for j in jobs if j]
    assert len(jobs) == 1
    j = jobs[0]
    assert j.company == "Propel Labs" and "Python" in j.title
    assert j.us_eligible is True and j.salary_min == 150000
    assert j.url == "https://news.ycombinator.com/item?id=101"


def test_scoring_prefers_matching_and_rejects_non_engineering(settings):
    good = Job(source="x", source_url="u1", title="Senior Python AI Automation Engineer", company="A", url="u1",
               remote=True, us_eligible=True, job_type="full_time", description="python llm agents typescript")
    sales = Job(source="x", source_url="u2", title="Account Executive", company="B", url="u2", remote=True)
    eu = Job(source="x", source_url="u3", title="Python Engineer", company="C", url="u3", remote=True, us_eligible=False, description="python")
    s_good, r_good = score_job(good, settings)
    assert s_good >= 70 and "US-eligible" in r_good
    assert score_job(sales, settings)[0] == 0
    assert score_job(eu, settings)[0] < settings.min_score


def test_dedupe_merges_sources():
    a = Job(source="Remotive", source_url="https://r/1", title="Senior Python AI Automation Engineer", company="Acme AI", url="https://r/1")
    b = Job(source="Remote OK", source_url="https://ok/9", title="Senior Python  AI Automation Engineer", company="ACME AI", url="https://ok/9", salary_min=150000)
    out = finder.dedupe([a, b])
    assert len(out) == 1 and out[0].also_on == ["Remote OK"] and out[0].salary_min == 150000


def test_find_jobs_end_to_end_offline(monkeypatch, settings):
    monkeypatch.setattr(remotive, "get_json", lambda *a, **k: load("remotive.json"))
    monkeypatch.setattr(remoteok, "get_json", lambda *a, **k: load("remoteok.json"))
    monkeypatch.setattr(himalayas, "get_json", lambda *a, **k: load("himalayas.json"))
    store = Store(settings.db_path)
    r = finder.find_jobs(settings, sources=["remotive", "remoteok", "himalayas", "adzuna", "usajobs"], store=store)
    s = r["summary"]["sources"]
    assert s["Adzuna"]["skipped"].startswith("missing ADZUNA")
    assert s["USAJOBS"]["skipped"].startswith("missing USAJOBS")
    titles = [j.title for j in r["jobs"]]
    assert "Account Executive" not in titles
    assert all(j.us_eligible is not False for j in r["jobs"])
    assert len(store.list_jobs()) == len(r["jobs"]) >= 2


def test_source_errors_do_not_abort(monkeypatch, settings):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(remotive, "get_json", boom)
    r = finder.find_jobs(settings, sources=["remotive"], persist=False)
    assert r["summary"]["sources"]["Remotive"]["error"] == "network down"


def test_hn_location_ignores_role_lists():
    c = {"id": 5, "created_at_i": 1791551358, "text": "Radar Labs | Software Engineers (SRE, ML, backend) | REMOTE (US) | NYC"}
    j = hn.parse_comment(c)
    assert "SRE" not in j.location and "REMOTE (US)" in j.location
