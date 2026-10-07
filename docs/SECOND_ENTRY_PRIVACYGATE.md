# Second-entry proposal: PrivacyGate
Verified 2026-10-06. Official source: https://gitlab-transcend.devpost.com/rules

## Verified event facts
Life After Code submission window: October 5, 2026 10:00 UTC to October 27, 2026 13:00 UTC (18:30 IST). Publication date not established.
Age: age of majority; user self-reports above 18. India is not in the explicit excluded-country list; other eligibility and conflict exclusions still apply. No numeric team cap found in visible rules.
Required sponsor technology: GitLab Duo Agent Platform. Contributor registration and provisioning required; not performed.
Cash pool: $45,000 USD from enumerated prizes, not credits. Each path has $4,000 assisted, $4,000 supervised, $5,000 hands-off. Special awards: two $5,000 stage-coverage awards, $5,000 environmental, $4,000 creative.
Judging: five equally weighted criteria—implementation, design, impact, innovation, presentation; Google Cloud deployment can add up to 0.2 points.
Reuse: Path A newly created on/after October 5. Path B existing MIT open-source project plus new automation after submission start. Public MIT GitLab repository, visible pipeline history, text description and public YouTube demo under three minutes required. Path B requires public deployment through approximately November 16.
Rank: provisional second research/build candidate after OpenCV; credible sponsor fit but unavailable Duo access is a blocker. No winning estimate.

## Proposal, not implementation
PrivacyGate rehearses school-app releases with entirely fictional student records, checks whether parent/student roles can access another child's records, and blocks promotion when privacy tests fail. Duo proposes a small fix, reruns role-isolation tests and produces a reviewable release report. A human approves final promotion.
Specific demo: deliberately introduce an insecure student-ID lookup; tests expose cross-student access; agent proposes ownership filtering; held-out negative tests and authorized-access tests gate the fix.
Measure: seeded defects detected, missed defects, unnecessary blocks and repair regressions. Avoid claiming generic security assurance.
Scope: one tiny attendance API, three roles, six seeded access-control regressions, no actual children or school data.
Kill criterion: cannot demonstrate meaningful Duo execution and visible GitLab pipeline history; a local script alone does not qualify.
Next tasks: draft API access matrix; implement fictional fixture API and adversarial tests; integrate sponsor platform only after legitimate provisioning. No registration, terms acceptance, paid deployment or license change to existing repo authorized by this brief.
