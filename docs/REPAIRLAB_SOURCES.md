# RepairLab source decision — 2026-10-07

## Selected calibration source: VCTK 0.92

The University of Edinburgh's official VCTK 0.92 record provides 110 English speakers, transcripts, controlled recording conditions and common passages across speakers. It is licensed CC BY 4.0. This makes a small attributed subset suitable for alignment, acoustic-feature and speaker-holdout validation.

- Official record and citation: https://doi.org/10.7488/ds/2645
- License: https://creativecommons.org/licenses/by/4.0/
- Required attribution is emitted into `manifest.json` by `repairlab.fetch_vctk_subset`.
- Claim limit: VCTK is clean read speech collected for speech technology. It is not proof of expert public-speaking quality and cannot establish a therapeutic outcome.

The official ZIP is 11,747,302,977 bytes. The range-based subset fetcher avoids downloading it whole:

```sh
python -m venv .source-venv
.source-venv/bin/pip install -r repairlab-source-requirements.txt
.source-venv/bin/python -m repairlab.fetch_vctk_subset private/vctk --speakers p225 p226 p227 --text-id 001
```

A private smoke fetch retrieved transcript-matched `p225_001`, `p226_001` and `p227_001` from the official archive. All three say “Please call Stella.” Durations were 2.051521, 2.798708 and 3.428771 seconds. Original FLAC SHA256 values were respectively `2439aaaaf7edc055d4051a1c43c3130582dcb4c3f4c797936fe118208d06b1bb`, `450ba3382afcfb0e3ec50d52296bc64a95be4b9bc89e0a10a5bfdc57f4756864` and `560d719e10b10f9da0c1b0a7485506fc9e4042c12b2667a7c5b50240c795a7ea`. Audio is intentionally not committed.

## Secondary oratory candidate: LibriVox Gettysburg collection

LibriVox's 150th-anniversary collection contains 15 readers of the same historic address and explicitly describes it as a major example of English oratory. Its public-domain policy allows reuse in the United States but tells users elsewhere to check local status. Until India-specific recording rights and exact transcript-version matching are reviewed, these recordings remain private comparison candidates—not publishable RepairLab data.

Three private downloads were integrity-checked but not committed:

| Reader code | Duration | SHA256 |
|---|---:|---|
| AMB | 124.551837 s | `bd2cd3537bc7e2935786b5d1fa264ad3e6acd92eca8aac727b89dbf5ce383427` |
| DJ | 115.487347 s | `918f83ef700be47b4a89976d741b8b62e8c95d00878ce8ac9bb44d80e4960d52` |
| DL | 139.075918 s | `7db49d8c8adc61bd59568176c74ca097337136cd47584b16b984d9f49aee6a49` |

Source: https://librivox.org/the-gettysburg-address-150th-anniversary-by-abraham-lincoln/ . Policy: https://librivox.org/pages/public-domain/ . The recordings may demonstrate real oratory variation later, but they must not become an unreviewed quality oracle.

## Rejected as public dataset sources for now

- W3C Kennedy excerpt: independent transcript exists, but embedded-recording derivative rights remain unclear. Private alignment check only.
- NASA Kennedy excerpt: real-audio runtime smoke test only; recording-specific derivative/publication review remains incomplete.
- TED and contemporary speeches: excluded unless an individual recording has explicit derivative and redistribution permission.

Source rights are now clear enough for a VCTK calibration subset, not for the final “effective delivery” reference set. The next gate is CPU alignment plus blind manual boundary labels on the selected VCTK clips; only then can milestone 1 be considered.
