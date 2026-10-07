"""Require explicit audio provenance before derivative-dataset publication.

This is a metadata gate, not a legal opinion or automatic license verification.
"""


def validate_source(source):
    required = ("source_url", "recording_id", "speaker_id", "text_id", "rights_url",
                "rights_basis", "reviewed_on", "baseline_rationale")
    for field in required:
        if not isinstance(source.get(field), str) or not source[field].strip():
            raise ValueError(f"Missing source metadata: {field}")
    for permission in ("redistribution_allowed", "derivatives_allowed", "rights_review_complete"):
        if source.get(permission) is not True:
            raise ValueError(f"Source publication blocked: {permission}")
    return dict(source)


def validate_split(training, held_out):
    """Require a strict speaker-and-text holdout, including all derivatives."""
    for field in ("speaker_id", "text_id", "recording_id"):
        train = {validate_source(s)[field] for s in training}
        test = {validate_source(s)[field] for s in held_out}
        if train & test:
            raise ValueError(f"Held-out leakage: {field}")
    if not training or not held_out:
        raise ValueError("Both split partitions must be nonempty")
