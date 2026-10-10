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

## Recording-specific archive evidence: Amherst address (checked 2026-10-08)

The JFK Library item `JFKWHA-234-003`, dated 26 October 1963, explicitly labels this sound recording **Public Domain**, identifies the White House Communications Agency as archival creator, and supplies a direct MP3 download. This is stronger evidence than an archive-wide assumption. The collection notice discusses United States copyright; this note does not assert a worldwide legal clearance.

- Item and preferred citation: https://www.jfklibrary.org/asset-viewer/archives/jfkwha-234-003
- Recording: https://static.jfklibrary.org/0x7drr3n0xjbx508575x6j24k601v320.mp3
- Official transcript candidate: https://www.arts.gov/about/kennedy-transcript
- Retrieved MP3: 35,247,638 bytes; ffprobe duration 881.162449 seconds; SHA256 `e1a8563994e6dc25a1d863f0dd12c2bcdfe5abb3d57720666823059d1e848461`.

The download succeeded and remains a private research candidate, not a committed/public dataset. The NEA transcript starts at the national-strength passage; do not assume it covers the full recording or includes applause, introductions, repetitions and deviations. Exact excerpt matching remains pending.

Provisional delivery rationale (a hypothesis, not listener evidence): the repeated power/poetry clauses offer parallel phrases for evaluating pause placement and emphasis. Select a short passage only after listening; historical importance alone is insufficient to label a speaker effective. Exclude quoted poetry from the first derivative set until its separate textual rights are assessed. One speaker cannot satisfy the speaker-holdout design.

Next: match a short prose passage to this recording, create independent start/end annotations before inspecting predicted boundaries, run CPU forced alignment, and report absolute boundary errors. Keep the reference-source gate open until delivery review and additional speakers are documented.

## Second speaker candidate: Obama at Lincoln Hall (checked 2026-10-08)

The archived White House item for President Obama's 12 March 2009 dedication remarks labels the specific video/audio `Public Domain`, links a downloadable MP3, and embeds the official transcript. A formal 53.9-second excerpt with repeated contrastive clauses was transcript-matched and successfully forced-aligned on CPU. Recording/excerpt hashes, delivery rationale, runtime and two-model diagnostic are in `docs/REPAIRLAB_OBAMA_ALIGNMENT.md`.

This adds a second speaker with recording-level evidence; it does not by itself satisfy the final corpus or human timing gate. Audio remains private and uncommitted.

## Third speaker candidate: Michelle Obama museum address (checked 2026-10-08)

The archived White House item for the 8 May 2014 National Medal for Museum and Library Services remarks labels the specific recording `Public Domain`, links its MP3 and embeds an event transcript. A 28.65-second passage with repeated challenges and a three-part parallel list matched all 75 official normalized words in an independent locator pass and successfully ran through the CPU forced aligner. Exact hashes, runtime, delivery rationale and disagreement limits are in `docs/REPAIRLAB_MICHELLE_ALIGNMENT.md`.

This yields three distinct provisional speakers/texts (Kennedy, Barack Obama and Michelle Obama), but does not turn three excerpts into a credible held-out evaluation. Blind human timing labels and additional excerpts remain required. A screened Biden item remains excluded because its transcript is explicitly “As Prepared for Delivery” and differs from the recording.

## Fourth-speaker precheck candidate: Biden in Nairobi (screened 2026-10-10)

The archived White House page for Vice President Joe Biden's 9 June 2010 address to university students in Nairobi labels the specific 26:01 recording **Public Domain**, links a downloadable MP3 and embeds a delivered-remarks transcript on the same page:

- Official recording/transcript page: https://obamawhitehouse.archives.gov/photos-and-video/video/vice-president-biden-speaks-kenya?page=5

This is a stronger precheck candidate than the previously excluded National Defense University item because the latter labels its text “As Prepared for Delivery.” The Nairobi page presents the transcript with delivered-speech markers, including laughter and applause, but exact audio/text agreement must still be measured rather than assumed.

Provisional delivery rationale: it is a sustained formal address to university students with explicit audience interaction and policy explanation, offering observable transitions and pause/emphasis choices. That is a hypothesis for expert-delivery suitability, not listener validation or a claim that the style is universally ideal.

No audio was downloaded and no alignment result is claimed in this screening increment. Before admission: retrieve the official MP3, record byte hash/duration, locate a short prose passage, verify every normalized word against audio, and run the same blind-boundary protocol. Keep this source out of the frozen dataset until those checks pass.

## Screened but not admitted (2026-10-10)

- Dr. Jill Biden's 4 August 2014 U.S.-Africa Leaders Summit recording is labelled Public Domain and offers MP3 download, but a matching delivered transcript was not located in this screen. Hold, do not infer text from captions or prepared materials.
- Biden's 18 February 2010 National Defense University page has recording-specific Public Domain metadata and audio, but its linked text is explicitly “As Prepared for Delivery.” It remains excluded until a transcript-matched excerpt is independently established.
- Additional Barack Obama archive recordings are well documented, but adding the same speaker does not resolve the present speaker-holdout bottleneck.
