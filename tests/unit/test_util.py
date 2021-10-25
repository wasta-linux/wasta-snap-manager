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
        snap = 'atom'
        offline_base_path = self.snaps_dir
        file_path = util.get_snap_file_path(snap, offline_base_path)
        self.assertEqual(file_path, offline_base_path / 'amd64' / 'atom_248.snap')

    def test_get_snap_file_path_false(self):
        snap = 'kiwi'
        offline_base_path = self.snaps_dir
        file_path = util.get_snap_file_path(snap, offline_base_path)
        self.assertFalse(file_path)

    def test_get_snap_yaml(self):
        snapfile = self.snaps_dir / 'amd64' / 'syncthing_501.snap'
        snap_yaml = util.get_snap_yaml(snapfile)
        self.assertEqual(type(snap_yaml), type(dict()))

    def test_get_snap_prerequisites(self):
        snapfile = self.snaps_dir / 'amd64' / 'snap-store_209.snap'
        snap_yaml = util.get_snap_yaml(snapfile)
        prereqs = ['gnome-3-28-1804', 'gtk-common-themes']
        self.assertEqual(util.get_snap_prerequisites(snap_yaml), prereqs)

    def test_get_offline_snap_details(self):
        snapfile = self.snaps_dir / 'amd64' / 'snap-store_209.snap'
        details = util.get_offline_snap_details(snapfile)
        for d, v in details.items():
            if d == 'base' or d == 'confinement' or d == 'summary':
                self.assertTrue(type(v), type(str()))
            elif d == 'prerequisites':
                self.assertEqual(type(v), type(list()))
