"""Startup hygiene: flags default off, no hardcoded home paths, no leaked keys."""

import re
from pathlib import Path

import chatty_flags
from chatty_paths import CHATTY_HOME, home_path

ROOT = Path(__file__).resolve().parents[1]


def test_legacy_loops_off_by_default(monkeypatch):
    for k in ("CHATTY_ENABLE_NARCOGUARD", "CHATTY_ENABLE_YOUTUBE", "CHATTY_ENABLE_X", "CHATTY_ENABLE_OPPORTUNITIES"):
        monkeypatch.delenv(k, raising=False)
    assert not chatty_flags.narcoguard_enabled()
    assert not chatty_flags.youtube_enabled()
    assert not chatty_flags.x_enabled()
    assert chatty_flags.opportunities_enabled()
    monkeypatch.setenv("CHATTY_ENABLE_X", "1")
    assert chatty_flags.x_enabled()


def test_paths_are_repo_relative():
    assert Path(home_path("chroma_db")).parent == CHATTY_HOME


def test_no_hardcoded_home_in_code():
    offenders = []
    for p in list(ROOT.glob("*.py")) + list(ROOT.glob("*.sh")):
        if p.name in ("chatty_paths.py", "test_system_integration.py"):
            continue
        if "/home/coden809/" in p.read_text(errors="ignore"):
            offenders.append(p.name)
    assert offenders == []


def test_no_nvidia_key_in_docs():
    pat = re.compile(r"nvapi-[A-Za-z0-9_-]{20,}")
    hits = [
        p.name for p in ROOT.glob("*.md")
        for m in pat.findall(p.read_text(errors="ignore"))
        if "your" not in m.lower()  # placeholders like nvapi-your-key-here are fine
    ]
    assert hits == []


def test_orchestrator_exits_nonzero_on_init_failure():
    src = (ROOT / "START_COMPLETE_AUTOMATION.py").read_text()
    main = src[src.index("async def main():"):]
    assert "sys.exit(1)" in main.split("await system.start()")[0]
