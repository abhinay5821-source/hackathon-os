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
Superseded on 2026-10-07: ClearRoute has a synthetic-tested prototype in PR #2 and PrivacyGate has a fictional-data baseline in PR #3. They remain incomplete entries.

## Active development focus — 2026-10-07

User authorized Track C after reviewing all four IIT Mandi briefs and an independent critique. Focus new engineering on RepairLab until its source-rights and real-audio alignment gates pass. Pause competing new-feature work on ClearRoute and PrivacyGate; preserve existing branches. Do not trade quality for simultaneous builds. Research may continue only when it does not displace the active critical path.

See docs/REPAIRLAB.md for six evidence-based readiness milestones, current test limits and October 13 conditional package target. The source/model gate is not yet passed; no registration or submission is authorized.

## Sole-target deadline priority — 2026-10-07

User directs that the existing eligible project with the earliest verified future submission deadline is the only engineering target. RepairLab remains the sole target: IIT Mandi closes October 15, 2026 at 00:15 IST. Preserve other projects paused; do not resume them automatically when source/alignment gates pass.

Comparison checked October 7: OpenCV closes October 26 Pacific time (header says 23:45 PDT while overview says 23:59; resolve before its submission); GitLab closes October 27 at 13:00 UTC (18:30 IST). These dates are later than IIT Mandi. Sources: https://multimodal-ai-hackathon-2026-7.devpost.com/updates/46710-problem-statements-are-live-multimodal-ai-hackathon-2026 ; https://opencv26.devpost.com/ ; https://gitlab-transcend.devpost.com/details/dates . After the active target is completed or expires, recheck eligibility and binding deadlines before selecting the next sole target.
