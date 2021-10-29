import os
import unittest

from pathlib import Path

from wsm import worker


class All(unittest.TestCase):
    def setUp(self):
        self.offline_snaps_dir = Path(__file__).parents[2] / 'var' / 'offline-snaps'
        self.snaps_dir = self.offline_snaps_dir / 'snaps'

    def tearDown(self):
        pass

    def test_get_assert_file(self):
        snap_name = 'atom_248'
        snap_file = self.snaps_dir / 'amd64' / f"{snap_name}.snap"
        assert_file = self.snaps_dir / 'amd64' / f"{snap_name}.assert"
        self.assertEqual(assert_file, worker.get_assert_file(snap_file))


if __name__ == '__main__':
    unittest.main()
