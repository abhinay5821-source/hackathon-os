# ClearRoute synthetic test report — 2026-10-06

Environment: Python 3.12, NumPy 2.3.5, OpenCV headless 5.0.0.93. Command: `python -m unittest discover -s tests -v`.

Result: **18 tests passed**. This is generated-fixture evaluation, not real-camera validation; test count is not detection accuracy.

| Synthetic condition | Expected behavior | Observed |
|---|---|---|
| Clear route | `clear` | Pass |
| Persistent in-route box | `review_required` with timestamp/image | Pass |
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
| Offline reviewer page | self-contained HTML with embedded evidence | Pass |
| Reviewer decision record | bounded decision, no identity field | Pass |

These cases are deliberately simple. They do not measure precision, recall, false-alert rate or reviewer time on real footage. Varied reflections, white physical obstructions, crowds, weather, compression damage and changed furniture remain untested. The reflection rule is intentionally conservative: it can trade a false alert for an uncertain result and still needs real validation.
