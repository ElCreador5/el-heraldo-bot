import tempfile
import unittest
from pathlib import Path
from custodio_evidence_index import prepare_index, find_reference, save_reference, remove_reference

class EvidenceIndexTests(unittest.TestCase):
    def test_recover_after_reopen_without_message_text(self):
        with tempfile.TemporaryDirectory() as root:
            db = str(Path(root) / "test.sqlite")
            prepare_index(db)
            save_reference(db, 1, 2, 3)
            self.assertEqual(find_reference(db, 1, 2), 3)
            save_reference(db, 1, 2, 4)
            self.assertEqual(find_reference(db, 1, 2), 3)
            self.assertIsNone(find_reference(db, 2, 2))
            remove_reference(db, 1, 2)
            self.assertIsNone(find_reference(db, 1, 2))

if __name__ == "__main__":
    unittest.main()
