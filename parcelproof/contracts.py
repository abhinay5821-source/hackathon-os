"""ParcelProof input and evidence contracts. No visual detection is implemented yet."""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass(frozen=True)
class VideoPair:
    packing: Path
    returned: Path
    case_id: str

    def validate(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        for video in (self.packing, self.returned):
            if not video.is_file():
                raise ValueError(f"Video file missing: {video.name}")
        if self.packing.resolve() == self.returned.resolve():
            raise ValueError("Packing and return recordings must be different files")

@dataclass(frozen=True)
class Evidence:
    kind: Literal["missing_item", "visible_damage"]
    packing_seconds: float
    return_seconds: float
    explanation: str

    def __post_init__(self) -> None:
        if self.kind not in ("missing_item", "visible_damage"):
            raise ValueError("Unsupported evidence kind")
        if self.packing_seconds < 0 or self.return_seconds < 0:
            raise ValueError("Evidence timestamps must be non-negative")
        if not self.explanation.strip():
            raise ValueError("Evidence requires an explanation")

@dataclass(frozen=True)
class ReviewResult:
    status: Literal["uncertain", "review_required", "no_discrepancy_observed"]
    evidence: tuple[Evidence, ...]
    limitations: tuple[str, ...]

def assemble_review(
    evidence: tuple[Evidence, ...], *, visibility_adequate: bool,
    alignment_verified: bool, analysis_completed: bool,
) -> ReviewResult:
    """Fail closed if footage or analysis cannot support a comparison.

    This assembles detector outputs; it does not analyze footage or establish fraud.
    """
    limitations = tuple(reason for ok, reason in (
        (visibility_adequate, "Insufficient item visibility"),
        (alignment_verified, "Recording alignment not verified"),
        (analysis_completed, "Visual comparison not completed"),
    ) if not ok)
    if limitations:
        return ReviewResult("uncertain", evidence, limitations)
    return ReviewResult(
        "review_required" if evidence else "no_discrepancy_observed",
        evidence, ("Visible evidence only; human review required",),
    )
