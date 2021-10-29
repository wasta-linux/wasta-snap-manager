import os
import unittest

from pathlib import Path

import setup


class All(unittest.TestCase):
    def setUp(self):
        self.vars = setup.get_vars()

    def tearDown(self):
        pass

    def test_get_version(self):
        # Asserting "True" to avoid having to update variable.
        self.assertTrue(self.vars.get('version'))

    def test_get_description(self):
        # Asserting "True" to avoid having to update description.
        self.assertTrue(self.vars.get('description'))

    def test_get_author(self):
        self.assertEqual(self.vars.get('author'), "Nate Marti")

    def test_get_email(self):
        self.assertEqual(self.vars.get('email'), "nate_marti@sil.org")

    def test_get_url(self):
        self.assertEqual(self.vars.get('url'), "https://github.com/wasta-linux/wasta-snap-manager")


if __name__ == '__main__':
    unittest.main()
