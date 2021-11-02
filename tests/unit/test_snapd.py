import gi
import os
import re
import shutil
import subprocess
import time
import unittest
import warnings

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from pathlib import Path

from wsm import snapd

# Assert*() methods here:
# https://docs.python.org/3/library/unittest.html?highlight=pytest#unittest.TestCase

class All(unittest.TestCase):
    def setUp(self):
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)

    def tearDown(self):
        pass

    def test_from_desktop(self):
        desktop_files = self.get_desktop_files(self.get_snap_names())
        missing_icons = []
        for desktop_file_item in desktop_files.items():
            name, icon = self.get_icon_from_desktop_file(desktop_file_item)
            # print(name + ':', icon)
            icon_file = self.find_icon(name, icon)
            #print(name + ':', icon_file)
            if not Path(icon_file).is_file():
                missing_icons.append(icon)
        self.assertEqual(missing_icons, [])
        # TODO: assert that icon is findable?

    @unittest.skip("incomplete")
    def test_from_meta_gui(self):
        pass

    def test_context_manager(self):
        with snapd.Snap() as snap:
            sys_info = snap.system_info()
        self.assertTrue(sys_info)

    def test_get_system(self):
        with snapd.Snap() as snap:
            conf = snap.get('system')
        self.assertTrue(isinstance(conf, dict))

    def test_get_refresh_list(self):
        with snapd.Snap() as snap:
            refreshes = snap.get_refresh_list()
        self.assertTrue(isinstance(refreshes, list))

    def test_get_snap_info(self):
        with snapd.Snap() as snap:
            info = snap.info('core')
        self.assertTrue(isinstance(info, dict))

    def get_snap_names(self):
        # Get list of snap names from snap dictionaries.
        with snapd.Snap() as s:
            names = [snap['name'] for snap in s.list()]
        return names

    def get_desktop_files(self, names):
        desktop_files = {}
        for name in names:
            snap_root = Path('/snap', name)
            subdirs = [s for s in snap_root.iterdir() if s.is_dir()]
            SNAP = sorted(subdirs, reverse=True)[0]

            poss_desktop_files = sorted(Path(SNAP).rglob('*' + name +'*.desktop'), reverse=True)
            desktop_file = poss_desktop_files[0] if poss_desktop_files else Path()

            if desktop_file.is_file():
                desktop_files[name] = desktop_file
        return desktop_files

    def get_icon_from_desktop_file(self, desktop_file_dict):
        name, desktop_file = desktop_file_dict
        with open(desktop_file) as file:
            contents = file.read()
            icon_line = re.search('^Icon=.*$', contents, re.MULTILINE)
            icon = icon_line.group(0).split('=')[1]
            return name, icon

    def find_icon(self, snap_name, icon_name):
        snap_root = Path('/snap', snap_name)
        subdirs = [s for s in snap_root.iterdir() if s.is_dir()]
        SNAP = sorted(subdirs, reverse=True)[0]

        icon_theme_default = Gtk.IconTheme.get_default()
        icon_theme_default.append_search_path(str(Path(SNAP, 'usr', 'share', 'icons')))
        if icon_name.split('/')[0] == '${SNAP}':
            # Relative path given.
            icon_name = str(SNAP) + "/" + "/".join(icon_name.split('/')[1:])
        elif icon_name[0] == '/':
            # Relative path given, but masquerading as absolute path.
            icon_name = str(SNAP) + icon_name

        if Path(icon_name).is_file():
            icon_file = icon_name
        elif icon_theme_default.lookup_icon(icon_name, 48, 0):
            icon_file = icon_theme_default.lookup_icon(icon_name, 48, 0).get_filename()
        else:
            # Icon not found.
            icon_file = icon_name

        return icon_file


if __name__ == '__main__':
    unittest.main()
