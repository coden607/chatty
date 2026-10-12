"""Feature flags for optional CHATTY subsystems.

Legacy loops (NarcoGuard funding/investor outreach, YouTube learning,
X/Twitter posting) are OFF by default so a fresh install starts quietly.
Set the env var to 1/true/yes/on to enable one.
"""

import os

_TRUE = {"1", "true", "yes", "on"}


def flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in _TRUE


def narcoguard_enabled() -> bool:
    """Investor workflows, GoFundMe updater, viral growth campaigns."""
    return flag("CHATTY_ENABLE_NARCOGUARD")


def youtube_enabled() -> bool:
    """Cole Medin / YouTube live learners (yt-dlp heavy, rate limited)."""
    return flag("CHATTY_ENABLE_YOUTUBE")


def x_enabled() -> bool:
    """X/Twitter automated posting."""
    return flag("CHATTY_ENABLE_X")


def opportunities_enabled() -> bool:
    """Job finder + Cortese prospect finder loop (on by default)."""
    return flag("CHATTY_ENABLE_OPPORTUNITIES", default=True)
