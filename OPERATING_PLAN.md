# Hackathon OS

## Goal
Research up to 15 legitimate cash-prize hackathons, shortlist six, and build a small number of tested entries solving concrete problems. Rankings are feasibility judgments, not promises of winning.

## Research baseline
Official rules reviewed on 2026-10-05. Recheck before registration or submission.

| Event | Official rules | Current disposition |
|---|---|---|
| OpenCV | https://opencv26.devpost.com/rules | First build candidate; remaining geography, reuse and deliverables checks pending |
| Amazon Build Ship Shape | https://amazonappdev2026.devpost.com/rules | Conditional shortlist; entrant eligibility unresolved |
| GitLab Life After Code | https://gitlab-transcend.devpost.com/rules | Conditional shortlist; needs GitLab Duo access |
| Qloo | https://qloo.devpost.com/rules | Conditional shortlist; needs API access |
| Nebius x NVIDIA | https://nebiusglobalaihackathon.devpost.com/rules | Conditional shortlist; requires Nebius runtime and NVIDIA open-source model |
| YouCam | https://youcam-api-skin-ai-ecommerce.devpost.com/rules | Conditional shortlist; needs API access |
| AWS CDS | https://aws-cds-partner.devpost.com/rules | Hold: AWS Partner affiliation required |
| Monad Metropolis | https://www.risein.com/monad/monad-metropolis-hackathon | Watch: conflicting deadline fields; binding rules and prize composition unresolved |

## First proposed build: ParcelProof
Compare packing and return footage to highlight visible missing items or damage, with timestamps and evidence frames for a human reviewer. Do not infer fraud or automate accusations.

### Initial scope
Fixed camera; one parcel; three item types; consented footage. Return an uncertain outcome for occlusion, insufficient evidence or inadequate image quality. Start with deterministic OpenCV alignment and count baselines before model integration.

### Backlog
- [ ] Complete official OpenCV eligibility, team-size, registration, reuse and submission checks.
- [ ] Define input video and expected-result schema.
- [ ] Collect and label packing/return pairs, including harmless packaging changes and poor lighting.
- [ ] Split by recording session into development and held-out evaluation sets.
- [ ] Implement alignment, visibility checks, discrepancy candidates and evidence export.
- [ ] Measure false positives, missed discrepancies and reviewer time against manual review.
- [ ] Add required OpenCV 5 and meaningful AWS integration after verifying runtime availability.
- [ ] Prepare reproducible setup, limitations, benchmark report and demo.

## Progress rules
Record actual completed work, tests and blockers. Use feature branches for implementation. Keep credentials and personal data out of this public repository. Do not register, accept terms, spend money, submit entries or contact organizers without explicit authorization.

Background research is scheduled separately. Installing GitHub alone does not create continuous coding execution; repo access and execution capability must be independently verified.

## Current status
Planning initialized. No application code or benchmark exists yet.
