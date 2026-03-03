from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional


class ApplicationStatus(str, Enum):
    CREATED = "CREATED"
    INGESTED = "INGESTED"
    ANALYZED = "ANALYZED"
    SCORED = "SCORED"
    CAM_GENERATED = "CAM_GENERATED"


@dataclass
class Application:
    """
    Minimal application state model to track an appraisal
    across ingestion, analysis, scoring and CAM generation.
    """

    id: str
    company_name: str
    sector: str
    requested_limit: float
    status: ApplicationStatus = ApplicationStatus.CREATED
    features: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[Dict[str, Any]] = None
    engine_version: str = "rules-v0.1"
    policy_hash: Optional[str] = None
    policy_snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

