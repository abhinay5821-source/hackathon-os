"""Evaluate declared synthetic cases; this is not real-world validation."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from parcelproof.baseline import analyze
from parcelproof.fixtures import generate

EXPECTED = {
    'unchanged': 'no_discrepancy_observed',
    'missing': 'review_required',
    # Same two items, different positions: a correct semantic system should not flag loss.
    'rearranged': 'no_discrepancy_observed',
    'occluded': 'uncertain',
    'poor_light': 'uncertain',
    'camera_shift': 'uncertain',
    'unstable': 'uncertain',
    'localized_occlusion': 'uncertain',
    'illumination_drift': 'uncertain',
}


def evaluate(workdir):
    root = generate(Path(workdir)/'fixtures')
    rows=[]
    for name, expected in EXPECTED.items():
        actual=analyze(root/'packing.avi',root/(name+'.avi'),Path(workdir)/('out_'+name))['status']
        rows.append({'case':name,'expected':expected,'actual':actual,'correct':actual==expected})
    return {'synthetic_cases':len(rows),'correct':sum(row['correct'] for row in rows),
            'failures':[row for row in rows if not row['correct']], 'results':rows,
            'warning':'Synthetic evaluation is not real-world validation.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output')
    args=parser.parse_args()
    with TemporaryDirectory() as workdir:
        report=evaluate(workdir)
    rendered=json.dumps(report,indent=2)+'\n'
    if args.output: Path(args.output).write_text(rendered,encoding='utf-8')
    print(rendered,end='')


if __name__=='__main__': main()
