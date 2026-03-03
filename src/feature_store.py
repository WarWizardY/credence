from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .application import Application


FEATURE_STORE_DIR = Path("data") / "feature_store"


def log_application(app: Application) -> Path:
    """
    Persist the final feature vector and decision for a given application.
    This provides a simple, file-based feature store and decision trace.
    """
    FEATURE_STORE_DIR.mkdir(parents=True, exist_ok=True)
    path = FEATURE_STORE_DIR / f"{app.id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(app.to_dict(), f, ensure_ascii=False, indent=2)
    return path


def load_application(app_id: str) -> Dict[str, Any]:
    """
    Load a previously stored application record by ID.
    """
    path = FEATURE_STORE_DIR / f"{app_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"No stored record for application_id={app_id}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

