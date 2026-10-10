"""Portable filesystem locations for CHATTY.

Older modules hardcoded ``/home/coden809/CHATTY``. Everything now resolves
relative to ``CHATTY_HOME`` (env var) or, by default, this repository.
"""

import os
from pathlib import Path

CHATTY_HOME = Path(os.getenv("CHATTY_HOME") or Path(__file__).resolve().parent)
CHROMA_DIR = Path(os.getenv("CHATTY_CHROMA_DIR") or CHATTY_HOME / "chroma_db")
LOG_DIR = Path(os.getenv("CHATTY_LOG_DIR") or CHATTY_HOME / "logs")
CONTENT_DIR = Path(os.getenv("CHATTY_CONTENT_DIR") or CHATTY_HOME / "generated_content")


def home_path(*parts: str) -> str:
    """Return an absolute path string under CHATTY_HOME."""
    return str(CHATTY_HOME.joinpath(*parts))
