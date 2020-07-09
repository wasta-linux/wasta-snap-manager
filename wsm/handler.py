""" Signal handler module. """

import subprocess
import threading

from wsm import util
from wsm import worker
from wsm import wsmapp


class Handler():
    def gtk_widget_destroy(self, *args):
        wsmapp.app.quit()

    def on_button_settings_clicked(self, *args):
        try:
            subprocess.run(['pkexec', '/usr/bin/snap-settings'])
        except:
            # Snap Settings app not found?
            print("Some error occurred!")

    def on_button_source_online_toggled(self, button):
        target = worker.handle_button_online_source_toggled
        self.t_online_check = threading.Thread(target=target, args=(button,))
        self.t_online_check.start()

    def on_button_source_offline_file_set(self, folder_obj):
        folder = folder_obj.get_filename()

        # Remove any existing rows (placeholder, previous folder, etc.).
        children = wsmapp.app.listbox_available.get_children()
        for c in children:
            wsmapp.app.listbox_available.remove(c)

        # Set app-wide variables.
        wsmapp.app.updatable_offline_list = util.get_offline_updatable_snaps(folder)
        wsmapp.app.installable_snaps_list = util.get_offline_installable_snaps(folder)
        wsmapp.app.select_offline_update_rows(folder)

        # Populate available snaps rows.
        list = wsmapp.app.installable_snaps_list
        wsmapp.app.rows1 = wsmapp.app.populate_listbox_available(wsmapp.app.listbox_available, list)

    def on_button_update_snaps_clicked(self, *args):
        # Make sure on_button_source_online_toggled has finished before continuing.
        try:
            self.t_online_check.join()
        except AttributeError:
            pass
        target = worker.handle_button_update_snaps_clicked
        self.t_update_snaps = threading.Thread(target=target)
        self.t_update_snaps.start()

    def on_button_remove_snaps_clicked(self, *args):
        user = util.get_user()
        try:
            proc = subprocess.run(
                ['su', '-c', '/snap/bin/snap-store --mode=installed', user],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except:
            # Snap Store not installed?
            print(subprocess.stdout, subprocess.stderr)

    def on_install_button_clicked(self, button, snap):
        target = worker.handle_install_button_clicked
        self.t_install_snap = threading.Thread(target=target, args=(button, snap))
        self.t_install_snap.start()
