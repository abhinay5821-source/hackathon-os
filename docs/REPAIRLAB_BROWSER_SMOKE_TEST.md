# Windows annotation browser smoke-test record

Complete this record before collecting any human boundary labels. This checks browser controls only; it does not validate alignment accuracy.

## Environment

- Date/time with timezone:
- Operating system/version:
- Browser/version:
- Annotation-pack version: 8
- Package freshly extracted into a new folder: yes / no

## Required checks

| Check | Pass/fail | Observation |
|---|---|---|
| Audio plays |  |  |
| **Zoom to 3 seconds** narrows the visible range |  |  |
| **+20 ms** increases the displayed current time slightly |  |  |
| **Play visible section** stops near the visible-range end |  |  |

## Decision

- All four passed: yes / no
- If no, stop and identify the failed control; do not estimate word boundaries from the full-clip waveform.
- If yes, the limited prediction-blind annotation sample may begin. Do not describe this result as alignment-error evidence.

Do not include a personal name, private path, recording content, credentials or other identifying data in a public copy of this record.
