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

An implemented S3 publisher can bundle those four evidence files and request private server-side-encrypted storage:

```sh
python -m parcelproof.aws_publish demo-evidence --bucket YOUR_EXISTING_BUCKET --case-id demo-001
```

That command uses the standard AWS credential chain and performs a real upload, so run it only with an authorized existing bucket and understood costs. The project does not provision buckets or change bucket policies. No live AWS upload has been run by this project yet.

## Architecture

Streaming video decoding with only the final five frames retained → final-view stability score → median frame → lighting/occlusion/calibration-border guards → thresholded pixel differences and connected regions → JSON, annotated evidence PNGs and local HTML review page. A marked-border comparison is a limited fixed-camera check, not geometric registration. Timestamps identify the last decoded frame; the image is a temporal median of the final frames.

## Limits

Stable final views, visible border calibration marks, constant illumination and matching dimensions are required. Interior-only motion, localized occlusion, shadows and unrelated motion can escape guards or cause false flags. The decoder now uses bounded frame memory, but video decode time still grows with clip length. No trained object detector, identity matching, damage classification, real-footage benchmark, authentication or cloud deployment exists. Evidence is advisory and requires human review.

## Test report — 2026-10-06 UTC

Executed locally after a clean dependency installation: `python -m unittest discover -s tests -v`. Eleven tests passed. Eight cover the vision baseline and three cover the S3 adapter: encrypted private upload parameters and exact evidence contents, incomplete-bundle rejection before upload, and unsafe case-ID rejection. Runtime reports OpenCV 5.0.0 and NumPy 2.3.5. The PyPI wheel is pinned as `opencv-python-headless==5.0.0.93`. CLI also ran successfully, exported one change region at 1.9 seconds and built a 13,226-byte evidence bundle for the synthetic missing-item case. These checks demonstrate narrow synthetic behavior and an isolated fake-client AWS contract, not accuracy on real parcels or successful AWS deployment. No live AWS test was run.

## Next build tasks

1. Add tests for localized obstruction, illumination drift and deceptive interior-only camera movement.
2. Validate the S3 publisher against an authorized test bucket, including bucket policy, retention, IAM least privilege and retrieval; no credentials or spending authorized here.
3. Obtain consented real recordings and evaluate held-out scenes; report false flags and missed visible changes.
4. Verify final country/team/reuse terms and exact deliverables, then record the demo.
