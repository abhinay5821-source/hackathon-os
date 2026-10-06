# Status — 2026-10-06

Draft PR: https://github.com/abhinay5821-source/hackathon-os/pull/1
Branch: parcelproof/synthetic-baseline (not merged).

Product correction: customer-recorded unboxing is excluded from the intended workflow following user feedback. Packing-station missing-accessory checks are a proposed narrower direction, not a validated use case or implemented semantic detector. Current code remains a two-video visible-change baseline.

Latest check: 16 tests passed on 2026-10-06, including a test that explicitly records known failure behavior. The expanded ten-case synthetic benchmark returns 9/10 expected outcomes. It misses a removed low-saturation gray item and reports `no_discrepancy_observed`, a false negative. Passing unit tests do not equal detection accuracy.

Official overview checked 2026-10-06: https://opencv26.devpost.com/ now establishes substantive OpenCV 5 and a meaningful running AWS component, technical report, judge-accessible code, pinned setup/deployment/tests, architecture diagram, working endpoint or arranged screen-share, evaluation evidence and a video of no more than five minutes. Its deadline prose says 11:59 PM Pacific October 26 while the header says 11:45 PM PDT: use the earlier deadline. Prize header $20,250 includes compute-grant listings and conflicts with $12,000 competition awards in rules; do not advertise the larger figure as winable award cash. Geography exclusions, team cap and reuse remain unresolved.

Completed: runnable fixed-camera video baseline with bounded five-frame memory; timestamped PNG/JSON evidence and local HTML review page; uncertainty guards; six synthetic fixture types; and a private AES-256 S3 evidence uploader with input/path checks. Eleven local automated tests pass after clean dependency installation. The missing-item CLI and local bundle build succeeded. AWS tests use an injected fake client only; no live AWS operation or real-footage validation occurred.

Disposition: keep ParcelProof as a runnable reference prototype, but demote it from primary-entry status unless semantic recognition can be added and independently evaluated. Do not spend AWS resources on this baseline. Next actionable step is to evaluate a stronger OpenCV entry direction before further cloud work. Country/team/reuse details still require official verification. Not submission-ready.

See docs/PARCELPROOF.md and docs/OPENCV_SUBMISSION_DRAFT.md. No registration, submission or cloud resources created.
