"""Upload one ParcelProof evidence bundle to private, encrypted S3 storage."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

REQUIRED = ('review.json', 'review.html', 'packing.png', 'returned.png')
CASE_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$')


def build_bundle(evidence_dir):
    root = Path(evidence_dir)
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        raise ValueError('Incomplete evidence directory: ' + ', '.join(missing))
    review = json.loads((root / 'review.json').read_text(encoding='utf-8'))
    memory = BytesIO()
    with ZipFile(memory, 'w', ZIP_DEFLATED) as archive:
        for name in REQUIRED:
            archive.write(root / name, arcname=name)
    return memory.getvalue(), review


def publish(evidence_dir, bucket, case_id, *, client, prefix='parcelproof'):
    if not CASE_ID.fullmatch(case_id):
        raise ValueError('case_id must be 1-80 safe filename characters')
    if not bucket.strip():
        raise ValueError('bucket must not be empty')
    body, review = build_bundle(evidence_dir)
    key = f"{prefix.strip('/')}/{case_id}/evidence.zip"
    response = client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType='application/zip',
        ServerSideEncryption='AES256',
        Metadata={
            'parcelproof-status': str(review.get('status', 'unknown')),
            'human-review-required': 'true',
        },
    )
    return {'bucket': bucket, 'key': key, 'version_id': response.get('VersionId')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence_dir')
    parser.add_argument('--bucket', required=True)
    parser.add_argument('--case-id', required=True)
    parser.add_argument('--prefix', default='parcelproof')
    args = parser.parse_args()
    import boto3
    result = publish(args.evidence_dir, args.bucket, args.case_id,
                     client=boto3.client('s3'), prefix=args.prefix)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
