# ParcelProof — OpenCV submission draft, not submission-ready

## Description

Parcel reviewers often need to compare packing and return recordings manually. ParcelProof aims to shorten that review by presenting timestamped before/after frames and visible-change regions while retaining human judgment. The current local prototype uses OpenCV 5.0.0 to decode two fixed-camera recordings, check basic visibility, compare stable final views and export evidence. Poor lighting or broad occlusion produces an uncertain result. It makes no fraud accusation.

## Demonstrated today

Four explicitly synthetic scenes: unchanged parcel view, removed colored object, broad obstruction and poor light. Six automated checks pass. No real-world accuracy or time-saving claim has been measured. The implementation is a deterministic pixel baseline, not semantic item recognition.

## Proposed AWS architecture — unimplemented

Local OpenCV analysis → structured evidence bundle → private S3 evidence storage → authorized reviewer retrieval. Cloud integration must be implemented and exercised before claiming sponsor fit. No AWS resources were created, credentials supplied or cloud tests run.

## Demo script

1. State that the footage is generated synthetic data.
2. Generate fixtures and run the missing-case CLI.
3. Open the two PNGs and JSON; show the region and 1.9-second timestamps.
4. Run unchanged, occluded and poor-light cases and explain the status changes.
5. Show the test command and limitations. Do not show AWS as working until verified.

## Rules check — 2026-10-06

Official source: https://opencv26.devpost.com/rules

Deadline shown: October 26, 2026 11:45 PM PDT, equivalent to October 27 12:15 PM IST. Up to $12,000 cash: overall $5,000/$3,000/$2,000 and two $1,000 special awards. Overall judging weights technical execution 30%, innovation 20%, impact 20%, UX 10%, documentation 10%, and AWS cloud delivery/reproducibility/responsible operation 10%. OpenCV 5 is explicitly part of technical execution; AWS deployment quality is explicitly assessed. COOL and agentic methods are optional for overall awards.

Participants must be 13+ and each team member eligible. User self-reports above 18. India eligibility, maximum team size and pre-existing-code/reuse conditions are not established by the retrieved rules page. The page references later governing terms; do not infer unrestricted eligibility. Reports, code, architecture, instructions and video appear in the judging criteria, but exact required submission fields and video length remain unverified.

## Remaining checklist

- [x] Runnable local OpenCV 5 baseline and synthetic fixtures
- [x] Executed tests and honest test report
- [x] Description, architecture, limitations and demo script
- [ ] Meaningful working AWS integration and repeatable validation
- [ ] Consent-based real-footage evaluation
- [ ] Stronger stability/alignment/visibility guards
- [ ] Confirm India, team, reuse and exact deliverable rules
- [ ] Recorded demo and final required submission materials
- [ ] User reviews and performs registration/terms acceptance/submission
