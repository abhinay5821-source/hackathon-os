# PayPal AI Hackathon — verified candidate

Verified from the official overview and rules on 2026-10-07.

- Official pages: https://paypalaihackathon.devpost.com/ and https://paypalaihackathon.devpost.com/rules
- Submission deadline: 2026-11-12 12:00 Pacific Time, equivalent to 2026-11-13 01:30 IST under the published schedule.
- Eligibility: entrants must be above the age of majority where they reside. India is not among the listed exclusions; final eligibility still belongs to the organizer. Individuals, teams and organizations may enter. The rules page does not state a maximum team size.
- Prize composition: USD 67,500 in enumerated cash prizes, plus USD 2,250 in Render credits. The cash pool includes USD 12,000 / 8,000 / 5,000 overall awards; five USD 5,000 honorable-mention awards; and several cash sponsor awards.
- Required integration: PayPal developer platform in its free sandbox plus a meaningful AI component. Optional sponsor tools are not required.
- Existing work: permitted if significantly updated after the submission period began on 2026-10-01 and the update is explained. Third-party tools must be authorized and license-compliant.
- Required deliverables: working prototype; text description; reproducible setup instructions or hosted demo; public open-source repository with a visible license; tool disclosure; public YouTube demonstration under three minutes.
- Judging: pass/fail sponsor/API fit, followed by equally weighted technological implementation, design, potential impact, innovation and presentation.
- Testing access: judges must be able to run or interact with the build free of charge through the judging period. Secrets must not be committed; test access needs a safe documented handoff.

## Proposed entry: RefundRelay

RefundRelay helps a small online merchant resolve legitimate refund requests without forcing a customer through a long support exchange. It accepts a fictional support message and sandbox transaction, extracts the requested remedy and reason, checks the merchant's explicit policy, and prepares a bounded full-refund, partial-refund or escalation recommendation. A human must approve before the PayPal sandbox refund call is made.

This directly addresses customer-experience friction without auto-accusing either party. The demo should measure decision agreement against labelled fictional cases, unsupported-policy refusals, incorrect-transaction refusals and the number of actions requiring escalation. It must never claim fraud detection or production financial safety.

### Narrow feasibility slice

1. Use only PayPal sandbox transactions and fictional customers.
2. Retrieve one transaction/order and verify amount, currency and captured state.
3. Parse one customer message into a structured request with uncertainty.
4. Apply deterministic policy limits before presenting any recommendation.
5. Require a human confirmation token before a sandbox refund.
6. Store an auditable receipt without payment credentials or personal data.

### Kill criteria and blockers

- Hold the build if a legitimate PayPal developer sandbox cannot be provisioned without accepting terms or disclosing secrets publicly.
- Stop if the accessible APIs cannot demonstrate an actual sandbox refund end to end.
- Do not build a generic chatbot with a decorative PayPal button; PayPal must be central to the transaction and refund workflow.
- Do not register, accept event terms, publish a video or submit without explicit user action.

## Provisional ranking

Shortlist candidate, not a winning prediction. Prize potential and sponsor fit are strong; deadline runway is better than the October events. Main risks are heavy competition, required public open-source licensing, safe judge access and obtaining a working PayPal sandbox integration. No code has been started for this entry.
