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

Inspect `demo-evidence/review.json`, `packing.png` and `returned.png`. Replace `missing.avi` with `unchanged.avi`, `occluded.avi` or `poor_light.avi` to exercise the other cases. All generated recordings are explicitly synthetic. Output folders contain no private footage by default.

## Architecture

Video decoding → median of last five frames → lighting/occlusion/background guards → thresholded pixel differences and connected regions → JSON plus annotated evidence PNGs. A border comparison is a limited fixed-camera check, not geometric registration. Timestamps identify the last decoded frame; the image is a temporal median of the final frames.

## Limits

Video is currently decoded into memory; use short clips only. Stable final views, constant illumination and matching dimensions are required. Interior camera shifts, localized occlusion, shadows and unrelated motion can escape guards or cause false flags. No trained object detector, identity matching, damage classification, real-footage benchmark, authentication or cloud deployment exists. Evidence is advisory and requires human review.

## Test report — 2026-10-06 UTC

Executed locally: `python -m unittest discover -s tests -v`. Six tests passed: changed region plus timestamp and readable evidence images; unchanged scene; broad occlusion abstention; dark-scene abstention; missing-file rejection; identical-recording rejection. Runtime reports OpenCV 5.0.0 and NumPy 2.3.5. CLI also ran successfully and exported one change region at 1.9 seconds for the synthetic missing-item case. These checks demonstrate narrow synthetic behavior, not accuracy on real parcels. AWS tests were not run; no AWS integration exists yet.

## Next build tasks

1. Stream frames with bounded memory and add motion/stability guards plus tests for camera shifts and localized obstruction.
2. Add reviewer HTML showing evidence and explicit uncertainty.
3. Implement a meaningful AWS component: proposed S3 evidence persistence with private access, encryption and retention controls; no credentials or spending authorized here.
4. Obtain consented real recordings and evaluate held-out scenes; report false flags and missed visible changes.
5. Verify final country/team/reuse terms and exact deliverables, then record the demo.
