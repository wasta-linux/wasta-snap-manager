import os
import unittest

from pathlib import Path

from wsm import util


class All(unittest.TestCase):
    def setUp(self):
        self.offline_snaps_dir = Path(__file__).parents[2] / 'var' / 'offline-snaps'
        self.snaps_dir = self.offline_snaps_dir / 'snaps'

    def tearDown(self):
        pass

    def test_get_root_type_pkexec(self):
        # Set testing UID if not already present.
        uid_init = os.environ.get('PKEXEC_UID')
        if not uid_init:
            os.environ['PKEXEC_UID'] = '9999'

        root_type = util.get_root_type()
        self.assertEqual(root_type, 'pkexec')

        # Remove testing UID if set by test.
        if not uid_init:
            del os.environ['PKEXEC_UID']

    def test_get_root_type_sudo(self):
        # Set testing UID if not already present.
        uid_init = os.environ.get('SUDO_UID')
        if not uid_init:
            os.environ['SUDO_UID'] = '9999'

        root_type = util.get_root_type()
        self.assertEqual(root_type, 'sudo')

        # Remove testing UID if set by test.
        if not uid_init:
            del os.environ['SUDO_UID']

    def test_get_snap_file_path_true(self):
        tests_path = Path(f'{__file__}/../..').resolve()

        snap = 'atom'
        offline_base_path = self.snaps_dir
        file_path = util.get_snap_file_path(snap, offline_base_path)
        self.assertEqual(file_path, offline_base_path / 'amd64' / 'atom_248.snap')

    def test_get_snap_file_path_false(self):
        tests_path = Path(f'{__file__}/../..').resolve()

        snap = 'kiwi'
        offline_base_path = self.snaps_dir
        file_path = util.get_snap_file_path(snap, offline_base_path)
        self.assertFalse(file_path)
