import os
import unittest

from wsm import util


class All(unittest.TestCase):
    def setUp(self):
        pass

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

    def test_from_meta_gui(self):
        pass
