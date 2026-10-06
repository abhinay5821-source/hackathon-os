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

All names, attendance figures and marks are invented. This baseline contains no real children, school records, credentials, server, database or deployment.

## Sponsor gap

The official event requires GitLab Duo Agent Platform and visible GitLab pipeline history. Neither is implemented or claimed here. Contributor registration, terms acceptance, GitLab provisioning, public MIT repository, CI/CD history, deployment and the under-three-minute YouTube demo remain pending. A local audit by itself is not an eligible submission.

Proposed sponsor workflow after legitimate access: a merge request introduces one seeded defect; tests expose the cross-record access; Duo proposes the narrow ownership check; the pipeline reruns all positive and negative probes; a human reviews the resulting merge request and release report.
