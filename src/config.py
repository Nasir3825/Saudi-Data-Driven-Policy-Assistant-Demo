from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DEFAULT_MODEL = os.getenv("GROQ_MODEL", "auto").strip() or "auto"
APP_TITLE = "Saudi Data-Driven Policy Assistant"
DATA_SNAPSHOT_DATE = "2026-08-30"
