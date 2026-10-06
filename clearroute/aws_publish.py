"""AWS evidence publishing contract with injected boto3-compatible clients."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class S3Client(Protocol):
    def put_object(self, **kwargs): ...


class DynamoClient(Protocol):
    def put_item(self, **kwargs): ...


def publish_review_event(result_path: Path, evidence_path: Path, *, event_id: str, bucket: str, table: str, s3: S3Client, dynamodb: DynamoClient) -> dict:
    """Upload one review event using encrypted S3 and conditional DynamoDB state."""
    if not event_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in event_id):
        raise ValueError("event_id must contain only letters, numbers, hyphen or underscore")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "review_required":
        raise ValueError("Only review_required events may be published")
    if not evidence_path.is_file():
        raise ValueError("Evidence image does not exist")
    evidence_key = f"events/{event_id}/evidence.png"
    result_key = f"events/{event_id}/result.json"
    common = {"Bucket": bucket, "ServerSideEncryption": "AES256"}
    s3.put_object(**common, Key=evidence_key, Body=evidence_path.read_bytes(), ContentType="image/png", Metadata={"event-id": event_id, "purpose": "human-review"})
    s3.put_object(**common, Key=result_key, Body=json.dumps(result, sort_keys=True).encode("utf-8"), ContentType="application/json", Metadata={"event-id": event_id, "purpose": "human-review"})
    dynamodb.put_item(
        TableName=table,
        Item={
            "event_id": {"S": event_id},
            "state": {"S": "pending_review"},
            "analysis_reason": {"S": str(result.get("reason", "unknown"))},
            "evidence_key": {"S": evidence_key},
            "result_key": {"S": result_key},
        },
        ConditionExpression="attribute_not_exists(event_id)",
    )
    return {"event_id": event_id, "bucket": bucket, "evidence_key": evidence_key, "result_key": result_key, "state": "pending_review"}
