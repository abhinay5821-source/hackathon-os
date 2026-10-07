"""CPU CTC forced alignment from acoustic-model emissions.

This aligns a supplied transcript token sequence; it does not recognize audio.
Emission frames must come from a separately validated acoustic model.
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np


def align(log_probs, token_ids, duration_seconds, blank_id=0):
    scores = np.asarray(log_probs, dtype=float)
    tokens = list(token_ids)
    if scores.ndim != 2 or not scores.shape[0] or not tokens:
        raise ValueError("Nonempty time-by-vocabulary emissions and transcript required")
    if np.isnan(scores).any() or np.isposinf(scores).any():
        raise ValueError("Invalid emission values")
    if not math.isfinite(duration_seconds) or duration_seconds <= 0:
        raise ValueError("Positive finite duration required")
    if any(not isinstance(t, (int, np.integer)) for t in [blank_id, *tokens]):
        raise ValueError("Token IDs must be integers")
    if not 0 <= blank_id < scores.shape[1] or any(t == blank_id or not 0 <= t < scores.shape[1] for t in tokens):
        raise ValueError("Invalid transcript or blank token ID")
    # Standard CTC expansion: blank, token, blank, token, ... blank.
    states = [blank_id]
    for token in tokens:
        states.extend([token, blank_id])
    count, length = scores.shape[0], len(states)
    previous = np.full(length, -np.inf)
    previous[0] = scores[0, blank_id]
    previous[1] = scores[0, states[1]]
    back = np.full((count, length), -1, dtype=np.int32)
    for frame in range(1, count):
        current = np.full(length, -np.inf)
        for state, token in enumerate(states):
            candidates = [state]
            if state > 0:
                candidates.append(state - 1)
            # Repeated transcript tokens must pass through a blank.
            if state > 1 and token != blank_id and token != states[state - 2]:
                candidates.append(state - 2)
            predecessor = max(candidates, key=lambda s: previous[s])
            current[state] = previous[predecessor] + scores[frame, token]
            back[frame, state] = predecessor
        previous = current
    state = max((length - 1, length - 2), key=lambda s: previous[s])
    if not np.isfinite(previous[state]):
        raise ValueError("Transcript cannot be aligned to these emissions")
    path = [state]
    for frame in range(count - 1, 0, -1):
        state = int(back[frame, state])
        path.append(state)
    path.reverse()
    seconds_per_frame = duration_seconds / count
    spans = []
    for index, token in enumerate(tokens):
        frames = [f for f, state in enumerate(path) if state == 2 * index + 1]
        if not frames:
            raise ValueError("Incomplete alignment")
        spans.append({"token_index": index, "token_id": int(token),
                      "start_seconds": frames[0] * seconds_per_frame,
                      "end_seconds": (frames[-1] + 1) * seconds_per_frame})
    return {"tokens": spans, "timing_basis": "uniform emission-frame spacing",
            "warning": "Alignment is not a delivery score; timing and transcript accuracy need audio validation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("emissions", type=Path, help="NPY log-probabilities [time, vocabulary]")
    parser.add_argument("transcript_tokens", type=Path, help="JSON array of nonblank token IDs")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--blank", type=int, default=0)
    args = parser.parse_args()
    result = align(np.load(args.emissions, allow_pickle=False),
                   json.loads(args.transcript_tokens.read_text()), args.duration, args.blank)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
