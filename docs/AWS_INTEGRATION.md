# AWS integration contract — not deployed

`clearroute.aws_publish.publish_review_event` defines the intended minimum cloud boundary. It accepts already-configured boto3-compatible S3 and DynamoDB clients, uploads only `review_required` evidence, requests S3 server-side encryption, and creates a conditional `pending_review` record so an event ID cannot be overwritten silently.

The automated tests use in-memory fake clients. They do not authenticate to AWS, create resources, validate IAM, prove that a bucket blocks public access, exercise encryption at rest, or measure cost/latency. Therefore this contract does **not** yet satisfy the competition's meaningful-AWS requirement.

Before live use:

1. Provision a private S3 bucket with Block Public Access, encryption, lifecycle expiry and access logging.
2. Provision a DynamoDB table keyed by `event_id`, with point-in-time recovery and explicit retention handling.
3. Create least-privilege roles limited to the exact bucket prefix and table actions.
4. Add an authenticated reviewer endpoint and audit-safe decision update.
5. Run an integration test in an authorized AWS account; record region, resource configuration, latency and teardown.
6. Add budget alarms before generating any charge.

No credentials, account identifiers or infrastructure state belong in this public repository.
