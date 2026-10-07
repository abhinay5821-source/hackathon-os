# PrivacyGate — local fixture baseline

PrivacyGate is a proposed GitLab Life After Code entry. It tests whether a school-app release lets one student, guardian or teacher read another student's fictional record. The local baseline provides two synthetic records, an explicit seven-case access matrix, three opt-in seeded authorization defects and a JSON audit report.

Run the secure fixture:

```bash
PYTHONPATH=. python -m privacygate.audit
```

Demonstrate a caught regression:

```bash
PYTHONPATH=. python -m privacygate.audit --seed-defect missing_guardian_scope
```

Run the same fail-closed command used by the CI draft:

```bash
PYTHONPATH=. python -m privacygate.gate --output privacygate-report.json
```

The command exits `0` only when all seven probes match the policy and exits `1` when a seeded leak is detected. `.gitlab-ci.yml` runs this gate after the unit tests and retains the JSON report as an artifact. This configuration has been exercised locally only; it has not run in GitLab and does not satisfy the visible-pipeline requirement yet.

Run the local fictional-record API:

```bash
PYTHONPATH=. python -m privacygate.server --port 8080
curl -H "X-Actor-Id: student-a" -H "X-Actor-Role: student" http://127.0.0.1:8080/records/student-a
```

The API returns `401` without actor headers, `403` for a known but unauthorized record and `404` for an unknown record. Headers are deterministic test identities, not production authentication.

The repository also includes a minimal non-root container definition and an unauthenticated `/healthz` liveness endpoint. On a machine with Docker:

```bash
docker build -t privacygate-fixture .
docker run --rm -p 8080:8080 privacygate-fixture
curl http://127.0.0.1:8080/healthz
```

The HTTP behavior and health endpoint are tested locally. Docker is unavailable in the current execution environment, so the image build and container start remain unverified; no hosted deployment is claimed.

All names, attendance figures and marks are invented. This baseline contains no real children, school records, credentials, database or deployment.

## Sponsor gap

The official event requires GitLab Duo Agent Platform and visible GitLab pipeline history. Neither is implemented or claimed here. Contributor registration, terms acceptance, GitLab provisioning, public MIT repository, CI/CD history, verified deployment and the under-three-minute YouTube demo remain pending. A local audit by itself is not an eligible submission.

Proposed sponsor workflow after legitimate access: a merge request introduces one seeded defect; tests expose the cross-record access; Duo proposes the narrow ownership check; the pipeline reruns all positive and negative probes; a human reviews the resulting merge request and release report.
