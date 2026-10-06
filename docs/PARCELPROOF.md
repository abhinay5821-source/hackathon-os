# ParcelProof prototype

Compare two calibrated, fixed-camera videos and export timestamped before/after evidence for a human reviewer. This baseline flags visible changes; it does not identify fraud, item identity or damage.

## Run

Python 3.11+ recommended. From repository root:

```sh
python -m pip install -r requirements.txt
python -m parcelproof.fixtures demo-fixtures
python -m parcelproof.baseline demo-fixtures/packing.avi demo-fixtures/missing.avi --output demo-evidence
python -m unittest discover -s tests -v
```

Open `demo-evidence/review.html`, or inspect `review.json`, `packing.png` and `returned.png`. Replace `missing.avi` with `unchanged.avi`, `occluded.avi`, `poor_light.avi`, `camera_shift.avi` or `unstable.avi` to exercise the other cases. All generated recordings are explicitly synthetic. Output folders contain no private footage by default.

## Architecture

Streaming video decoding with only the final five frames retained → final-view stability score → median frame → lighting/occlusion/calibration-border guards → thresholded pixel differences and connected regions → JSON, annotated evidence PNGs and local HTML review page. A marked-border comparison is a limited fixed-camera check, not geometric registration. Timestamps identify the last decoded frame; the image is a temporal median of the final frames.

## Limits

Stable final views, visible border calibration marks, constant illumination and matching dimensions are required. Interior-only motion, localized occlusion, shadows and unrelated motion can escape guards or cause false flags. The decoder now uses bounded frame memory, but video decode time still grows with clip length. No trained object detector, identity matching, damage classification, real-footage benchmark, authentication or cloud deployment exists. Evidence is advisory and requires human review.

## Test report — 2026-10-06 UTC

Executed locally after a clean dependency installation: `python -m unittest discover -s tests -v`. Eight tests passed: changed region plus timestamp, readable images and review page; unchanged scene; broad occlusion abstention; dark-scene abstention; camera-shift abstention; unstable-final-view abstention; missing-file rejection; identical-recording rejection. Runtime reports OpenCV 5.0.0 and NumPy 2.3.5. The PyPI wheel is pinned as `opencv-python-headless==5.0.0.93`. CLI also ran successfully and exported one change region at 1.9 seconds for the synthetic missing-item case. These checks demonstrate narrow synthetic behavior, not accuracy on real parcels. AWS tests were not run; no AWS integration exists yet.

## Next build tasks

1. Add tests for localized obstruction, illumination drift and deceptive interior-only camera movement.
2. Implement a meaningful AWS component: proposed S3 evidence persistence with private access, encryption and retention controls; no credentials or spending authorized here.
3. Obtain consented real recordings and evaluate held-out scenes; report false flags and missed visible changes.
4. Verify final country/team/reuse terms and exact deliverables, then record the demo.
