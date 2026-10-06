# ClearRoute local prototype

ClearRoute compares a fixed-camera video with a configured clear reference and asks one narrow question: did visible change inside the route persist long enough to warrant human review? It does not recognize people or objects and must not be used as the sole safety control.

## Run

Use Python 3.11 or newer in a virtual environment:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m clearroute.fixtures synthetic-fixtures
python -m clearroute.analyze reference.png input.mp4 --output result.json
```

The fixture command writes explicitly synthetic MJPG/AVI clips. The analyzer CLI writes the status, reason, frame occupancy series, first evidence frame and timestamp to JSON, plus an annotated `.evidence.png` for a review event. The default route rectangle is a prototype constant; a real deployment needs a reviewed per-camera polygon and calibration workflow.

## Synthetic evaluation

The unit suite generates arrays rather than using real footage. Cases cover a clear route, persistent box, transient passage, outside-route object, poor light, global occlusion and camera shift. Passing these tests is only a feasibility result, not real-world validation.

## Known limitations

- The asserted synthetic shadow is simple and does not represent varied real shadows.
- Scene rearrangement, reflections, crowds, slow camera drift and weather are untested.
- Evidence metadata and a marked frame are produced; a reviewer UI is not implemented.
- No AWS component is implemented or validated.
- No consented real footage has been evaluated.
