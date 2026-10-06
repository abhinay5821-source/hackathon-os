import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

from parcelproof.aws_publish import publish


class FakeS3:
    def __init__(self): self.call = None
    def put_object(self, **kwargs):
        self.call = kwargs
        return {'VersionId': 'test-version'}


class AwsPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root/'review.json').write_text(json.dumps({'status':'review_required'}))
        for name in ('review.html','packing.png','returned.png'):
            (self.root/name).write_bytes(name.encode())
    def tearDown(self): self.tmp.cleanup()

    def test_upload_is_encrypted_private_bundle(self):
        client = FakeS3()
        result = publish(self.root, 'evidence-bucket', 'case-123', client=client)
        self.assertEqual(result['key'],'parcelproof/case-123/evidence.zip')
        self.assertEqual(client.call['ServerSideEncryption'],'AES256')
        self.assertNotIn('ACL',client.call)
        self.assertEqual(client.call['Metadata']['human-review-required'],'true')
        with ZipFile(BytesIO(client.call['Body'])) as archive:
            self.assertEqual(set(archive.namelist()),
                             {'review.json','review.html','packing.png','returned.png'})

    def test_incomplete_evidence_rejected_before_upload(self):
        (self.root/'returned.png').unlink(); client=FakeS3()
        with self.assertRaises(ValueError):
            publish(self.root,'bucket','case-1',client=client)
        self.assertIsNone(client.call)

    def test_unsafe_case_id_rejected(self):
        with self.assertRaises(ValueError):
            publish(self.root,'bucket','../private',client=FakeS3())


if __name__ == '__main__': unittest.main()
