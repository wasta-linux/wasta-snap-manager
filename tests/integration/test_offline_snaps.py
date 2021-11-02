import gi
# import os
import shutil
import subprocess
import time
import unittest

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from pathlib import Path

from wsm import util
from wsm import wsmapp
from wsm import wsmwindow

# Assert*() methods here:
# https://docs.python.org/3/library/unittest.html?highlight=pytest#unittest.TestCase

class All(unittest.TestCase):
    def setUp(self):
        self.offline_snaps_dir = Path(__file__).parents[2] / 'var' / 'offline-snaps'
        self.snaps_dir_archless = self.offline_snaps_dir / 'snaps_archless'
        self.snaps_dir_empty = self.offline_snaps_dir / 'snaps_empty'
        self.snaps_dir_sorted = self.offline_snaps_dir / 'snaps'

    def tearDown(self):
        pass

    def test_listed_from_1_folder(self):
        snaps_dir = self.snaps_dir_sorted / 'amd64'
        from_app, from_cmd = self.get_lists(snaps_dir)
        self.assertListEqual(from_app, from_cmd)

    def test_listed_from_1_folder_empty(self):
        snaps_dir = self.snaps_dir_empty
        from_app, from_cmd = self.get_lists(snaps_dir)
        self.assertListEqual(from_app, from_cmd)

    def test_listed_from_sorted_folders(self):
        snaps_dir = self.snaps_dir_sorted
        from_app, from_cmd = self.get_lists(snaps_dir)
        self.assertListEqual(from_app, from_cmd)

    @unittest.skip("superseded")
    def test_sorted_into_arch_folders(self):
        print() # blank line to set apart app fuction output
        snaps_dir = self.snaps_dir_archless
        list_init = [i.name for i in snaps_dir.iterdir()]

        # Copy snaps in snaps_dir to "wasta-offline".
        wasta_offline_dir = Path(snaps_dir.parents[0], 'wasta-offline')
        out_dir = Path(wasta_offline_dir, 'local-cache', 'snaps')
        Path.mkdir(out_dir, mode=0o777, parents=True)
        for file in snaps_dir.iterdir():
            shutil.copy(file, out_dir)

        util.wasta_offline_snap_cleanup(wasta_offline_dir)
        list_final = []
        for child in out_dir.iterdir():
            if child.is_dir():
                sublist = [i.name for i in Path(child).iterdir()]
                list_final.extend(sublist)
        self.assertListEqual(sorted(list_init), sorted(list_final))
        # Remove temp wasta-offline dir.
        shutil.rmtree(wasta_offline_dir)

    def get_lists(self, snaps_dir):
        # Get list from app.
        offline_list = util.list_offline_snaps(snaps_dir)
        offline_filenames_by_app = sorted([i['file_path'] for i in offline_list])

        # Get list from terminal commands.
        cmd = subprocess.run(
            ['find', snaps_dir, '-name', '*.snap'],
            stdout=subprocess.PIPE
        )
        offline_filenames_by_cmd = sorted(cmd.stdout.decode().splitlines())
        return offline_filenames_by_app, offline_filenames_by_cmd


class Avail(unittest.TestCase):
    def setUp(self):
        self.offline_snaps_dir = Path(__file__).parents[2] / 'var' / 'offline-snaps'
        self.snaps_dir = self.offline_snaps_dir / 'snaps'

    def tearDown(self):
        pass

    def test_listed(self):
        snaps_avail_offline = util.get_offline_installable_snaps(self.snaps_dir)
        availables_by_app = [i['name'] for i in snaps_avail_offline]

        snaps_offline = util.list_offline_snaps(self.snaps_dir)
        cmd = subprocess.run(['snap', 'list'], stdout=subprocess.PIPE)
        snaps_installed = [s.split()[0] for s in cmd.stdout.decode().splitlines()[1:]]
        availables_by_cmd = []
        for item in snaps_offline:
            if item['name'] not in snaps_installed:
                availables_by_cmd.append(item['name'])

        self.assertListEqual(sorted(availables_by_app), sorted(availables_by_cmd))

    @unittest.skip("incomplete")
    def test_shown(self):
        pass


@unittest.skip("incomplete")
class Upd8(unittest.TestCase):
    def setUp(self):
        self.offline_snaps_dir = Path(__file__).parents[2] / 'var' / 'offline-snaps'
        self.snaps_dir = self.offline_snaps_dir / 'snaps'

    def tearDown(self):
        pass

    def test_listed(self):
        snaps_avail_offline = util.get_offline_installable_snaps(self.snaps_dir)
        availables_by_app = [i['name'] for i in snaps_avail_offline]

        snaps_offline = util.list_offline_snaps(self.snaps_dir)
        cmd = subprocess.run(['snap', 'list'], stdout=subprocess.PIPE)
        snaps_installed = [s.split()[0] for s in cmd.stdout.decode().splitlines()[1:]]
        availables_by_cmd = []
        for item in snaps_offline:
            if item['name'] not in snaps_installed:
                availables_by_cmd.append(item['name'])
        self.assertListEqual(sorted(availables_by_app), sorted(availables_by_cmd))

    def test_shown(self):
        raise Exception("Test not yet implemented.")

class ListBoxPane(unittest.TestCase):
    def setUp(self):
        #app = wsmapp.app
        app = ''
        # fake "app" needs method "populate_listbox_available"
        self.pane = wsmwindow.InstalledListBoxPane(app)

    def tearDown(self):
        pass

    # Stolen from Kiwi
    def refresh_gui(self, delay=0):
      while Gtk.events_pending():
          Gtk.main_iteration_do(self) #block=False
      time.sleep(delay)


if __name__ == '__main__':
    unittest.main()
