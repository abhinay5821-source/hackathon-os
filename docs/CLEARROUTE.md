# ClearRoute local prototype

ClearRoute compares a fixed-camera video with a configured clear reference and asks one narrow question: did visible change inside the route persist long enough to warrant human review? It does not recognize people or objects and must not be used as the sole safety control.

## Run

Use Python 3.11 or newer in a virtual environment:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m clearroute.fixtures synthetic-fixtures
python -m clearroute.analyze reference.png input.mp4 --output result.json
python -m clearroute.review result.json --output review.html
```

The fixture command writes explicitly synthetic MJPG/AVI clips. The analyzer CLI writes the status, reason, frame occupancy series, first evidence frame and timestamp to JSON, plus an annotated `.evidence.png` for a review event. The review command embeds the result and evidence in a self-contained offline HTML page. The default route rectangle is a prototype constant; a real deployment needs a reviewed per-camera polygon and calibration workflow.

## Synthetic evaluation

The unit suite generates arrays rather than using real footage. Cases cover a clear route, persistent box, transient and intermittent blockage, outside-route object, simple shadow, gradual dimming, poor light, global occlusion, abrupt camera shift and slow camera drift. Passing these tests is only a feasibility result, not real-world validation.

## Known limitations

- The asserted synthetic shadow is simple and does not represent varied real shadows.
- A persistent bright synthetic reflection produces a false `review_required` result. Reflection handling is therefore a measured blocker, not a passed accuracy case.
- Scene rearrangement, varied reflections, crowds, weather and compression damage remain untested.
- Evidence metadata, a marked frame and offline reviewer page are implemented; reviewer decisions are not persisted.
- No AWS component is implemented or validated.
- No consented real footage has been evaluated.
