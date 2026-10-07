# ClearRoute synthetic test report — 2026-10-07

Environment: Python 3.12, NumPy 2.3.5, OpenCV headless 5.0.0.93. Command: `python -m unittest discover -s tests -v`.

Result: **33 tests passed** on the evidence-export increment based on remote branch head `bc4a0ecf88614a26787572135490f49af2284655`. Command used an isolated Python venv with the pinned dependencies. The one-command demo also completed and produced a JSON result, marked evidence PNG and self-contained review page. This is generated-fixture/fake-client evaluation, not real-camera or live-AWS validation; test count is not detection accuracy.

New regression checks: a synthetic 20-FPS AVI produces frame-index/20 timestamps and writes evidence into a previously absent nested directory; an image-write failure raises instead of publishing a fresh result JSON; zero, negative and non-finite frame rates are rejected. Video timing assumes constant frame rate, and persistence remains frame-count based. These checks do not validate variable-frame-rate footage.

| Synthetic condition | Expected behavior | Observed |
|---|---|---|
| Clear route | `clear` | Pass |
| Persistent in-route box | `review_required` with timestamp/image | Pass |
| Stable white box | `review_required`, not reflection uncertainty | Pass |
| Colored box with fluctuating glare | `review_required` | Pass |
| Transient passage | `clear` | Pass |
| Intermittent short blockages | `clear` under current persistence rule | Pass |
| Object outside route | `clear` | Pass |
| Simple shadow | `clear` | Pass |
| Gradual dimming | `uncertain`, never review alert | Pass |
| Poor light | `uncertain` | Pass |
| Large occlusion | `uncertain` | Pass |
| Abrupt camera shift | `uncertain` | Pass |
| Slow camera drift | eventually `uncertain` | Pass |
| Camera vibration | `uncertain` | Pass |
| Persistent bright reflection | avoid false blockage alert | `uncertain` (`possible_reflection`) |
| Empty stream | `uncertain` | Pass |
| AVI-to-result/evidence path | JSON and marked PNG written | Pass |
| Encoded AVI reflection/white-object distinction | reflection uncertain; white/glare boxes review | Pass |
| Offline reviewer page | self-contained HTML with embedded evidence | Pass |
| Reviewer decision record | bounded decision, no identity field | Pass |
| AWS publishing contract | encrypted S3 request + conditional DynamoDB state using fakes | Pass |
| AWS non-review guard | clear/uncertain events are not uploaded | Pass |
| Infrastructure policy checks | encrypted/private/expiring storage and scoped writes declared | Pass |
| Authenticated review endpoint | missing/wrong token denied; bounded decision accepted | Pass |
| Evaluation provenance and metrics | synthetic provenance required; errors and uncertainty separated | Pass |
| One-command demo bundle | synthetic clip, JSON, evidence PNG and offline review generated | Pass |

These cases are deliberately simple. They do not measure precision, recall, false-alert rate or reviewer time on real footage. Varied reflections and white objects, crowds, weather, compression damage and changed furniture remain untested. The reflection rule combines brightness, low saturation and temporal fluctuation; it still needs real validation.
