from pathlib import Path
import tempfile
import unittest

from wikinav.sources import check_file


class AcquisitionIntegrityTests(unittest.TestCase):
    def test_same_size_corruption_is_rejected(self):
        source={'name':'fixture','bytes':3,'sha256':'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'fixture'
            path.write_bytes(b'abc');check_file(path,source)
            path.write_bytes(b'abd')
            with self.assertRaisesRegex(ValueError,'sha256 mismatch'):
                check_file(path,source)
