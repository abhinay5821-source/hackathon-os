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
python -m clearroute.decision result.json dismissed --note "Reflection on route" --output decision.json
```

The fixture command writes explicitly synthetic MJPG/AVI clips. The analyzer CLI writes the status, reason, frame occupancy series, first evidence frame and timestamp to JSON, plus an annotated `.evidence.png` for a review event. The review command embeds the result and evidence in a self-contained offline HTML page. The decision command records one bounded human outcome without reviewer identity or automatic action. The default route rectangle is a prototype constant; a real deployment needs a reviewed per-camera polygon and calibration workflow.

## Local reviewer endpoint

Set a temporary token and run `CLEARROUTE_REVIEW_TOKEN='replace-with-a-long-random-value' python -m clearroute.server result.json`. The service binds to `127.0.0.1:8080` by default. `GET /review` and `POST /decision` require an `Authorization: Bearer <token>` header.

The endpoint uses constant-time token comparison, disables caching and accepts only those fixed routes. It is for a controlled local demonstration or arranged screen-share. It has no TLS, user accounts, rate limiting, session management or public-hosting hardening.

## Synthetic evaluation

The unit suite generates arrays rather than using real footage. Cases cover a clear route, persistent box, transient and intermittent blockage, outside-route object, simple shadow, gradual dimming, poor light, global occlusion, abrupt camera shift and slow camera drift. Passing these tests is only a feasibility result, not real-world validation.

## Known limitations

- The asserted synthetic shadow is simple and does not represent varied real shadows.
- A bright, low-saturation change must also fluctuate over time before it is labeled `possible_reflection`. The synthetic stable white box and colored box with glare still require review. This remains a heuristic, not reflection understanding.
- Scene rearrangement, varied reflections, crowds, weather and compression damage remain untested.
- Evidence metadata, a marked frame, offline reviewer page and local decision record are implemented.
- No AWS component is implemented or validated.
- No consented real footage has been evaluated.
