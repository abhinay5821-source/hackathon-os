# OpenCV pivot decision — 2026-10-06

## Decision

Promote **ClearRoute** for feasibility testing: a privacy-preserving fixed-camera monitor for persistent obstruction of marked emergency exits and accessible routes. ParcelProof remains a reference prototype because its adversarial synthetic evaluation exposed a missing-item false negative.

This is a proposal, not a validated safety system. It must never be the sole control for emergency access.

## Why this direction

The visual question is deliberately narrow: “Has a predefined route polygon been persistently occupied compared with its clear baseline?” Object identity is unnecessary. Existing staff-operated cameras can provide input; customers perform no additional action. Evidence goes to a human facilities reviewer rather than triggering punishment or emergency action automatically.

| Candidate | Real problem | OpenCV depth | Fast honest evaluation | Main weakness | Decision |
|---|---:|---:|---:|---|---|
| ClearRoute — exit/access-route obstruction | High | Medium | High | Shadows, crowds and camera movement | Test first |
| NearMiss — trajectory collision warning | High | High | Low | Requires detection/tracking data and calibration | Hold |
| DrainWatch — drain blockage/water level | Medium-high | Medium | Medium | Site/weather data and camera fouling | Hold |

## Narrow prototype contract

- One fixed camera and one configured route polygon.
- Establish a clear reference view.
- Use OpenCV 5 background/change analysis, morphology and persistence across frames.
- Output `clear`, `review_required`, or `uncertain` for camera shift, poor light or inadequate visibility.
- Export timestamped evidence and the reason for review.
- No face recognition, identity tracking, biometric inference or automatic emergency decision.

## Synthetic evaluation before any cloud work

Generate: clear route; box persists in route; person-shaped transient passes; shadow/illumination change; camera shift; partial occlusion; obstruction outside polygon. Required outcomes: persistent in-route box → review; transient and outside-route objects → clear; ambiguous quality/camera conditions → uncertain.

Kill the direction if the deterministic baseline cannot separate persistent obstruction from transient passage and lighting changes in generated tests, or if a small consented fixed-camera test later produces frequent false alerts.

## Proposed AWS role — unimplemented

Upload only review events and evidence to private encrypted S3; write event state to DynamoDB; provide a small authenticated reviewer endpoint. No alerts are sent automatically in the prototype. AWS resources, IAM, retention, retrieval and costs remain unvalidated and require separate authorization.

## Competition fit and remaining proof

The official overview requires substantive OpenCV 5 analysis and a meaningful component running on AWS. It lists safety and accessibility among suggested areas and requires a technical report, judge-accessible code, pinned build/deployment/test instructions, an architecture diagram, a working endpoint or arranged screen-share, evaluation evidence and a judge-accessible video no longer than five minutes.

Before calling this an entry: build and test the local baseline; document failure cases; validate on consented footage; implement and exercise AWS; confirm official geography/team/reuse terms; prepare the required endpoint/demo, report, diagram and video.
