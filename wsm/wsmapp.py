""" Main GUI module. """

import gi
import logging
import os
import subprocess

from pathlib import Path
current_file_path = Path(__file__)

gi.require_version("Gtk", "3.0")
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from wsm import cmdline
from wsm import guiparts
from wsm import handler
from wsm import util
from wsm import snapd
from wsm import wsmwindow


class WSMApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='org.wasta.apps.wasta-snap-manager',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.add_main_option(
            'version', ord('V'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
            'Print snapd version number.', None
        )
        self.add_main_option(
            'snaps-dir', ord('s'), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
            'Update snaps from offline folder.', '/path/to/wasta-offline'
        )
        self.add_main_option(
            'online', ord('i'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
            'Update snaps from the online Snap Store.', None
        )

        # Get UI location based on current file location.
        self.ui_dir = '/usr/share/wasta-snap-manager/ui'
        if str(current_file_path.parents[1]) != '/usr/share/wasta-snap-manager':
            self.ui_dir = str(current_file_path.parents[1] / 'data' / 'ui')

        # Define app-wide variables.
        self.runmode = ''
        self.installed_snaps_list = snapd.snap.list()
        self.installable_snaps_list = []
        self.updatable_offline_list = []
        #self.updatable_online_list = []
        self.updatable_online_dict = {}

    def do_startup(self):
        # Define builder and its widgets.
        Gtk.Application.do_startup(self)

        # Get widgets from glade file. (defined in __init__)
        self.builder = Gtk.Builder()
        self.builder.add_from_file(self.ui_dir + '/snap-manager.glade')

        self.grid_source = self.builder.get_object('grid_source')
        self.button_source_online = self.builder.get_object('button_source_online')
        self.button_remove_snaps = self.builder.get_object('button_remove_snaps')
        self.label_button_source_online = self.builder.get_object('label_button_source_online')
        self.button_source_offline = self.builder.get_object('button_source_offline')
        self.window_installed_snaps = self.builder.get_object("scrolled_window_installed")
        self.window_available_snaps = self.builder.get_object("scrolled_window_available")
        self.label_can_update = self.builder.get_object('label_can_update')

    def do_activate(self):
        # Verify execution with elevated privileges.
        if os.geteuid() != 0:
            bin = '/usr/bin/wasta-snap-manager'
            print("wasta-snap-manager needs elevated privileges; e.g.:\n\n$ pkexec", bin, "\n$ sudo", bin)
            exit(1)

        # Start GUI logging
        util.set_up_logging()
        util.log_snapd_version(util.get_snapd_version())
        util.log_installed_snaps(self.installed_snaps_list)

        # Define window and make runtime adjustments.
        self.window = self.builder.get_object('window_snap_manager')
        self.window.set_icon_name('wasta-snap-manager')
        self.add_window(self.window)
        self.window.show()

        # Hide label_can_update b/c it seems to be confusing, but saving just in case.
        self.label_can_update.hide()
        # Hide button_remove_snaps b/c it doesn't launch right when run as installed app.
        self.button_remove_snaps.hide()

        # Make GUI initial adjustments.
        self.user, self.start_folder = util.guess_offline_source_folder()
        self.button_source_offline.set_current_folder(self.start_folder)

        # Get ListBox "panes" from other module, add to sub-windows, & show.
        self.avail_lb_pane = wsmwindow.AvailableListBoxPane(self)
        self.instd_lb_pane = wsmwindow.InstalledListBoxPane(self)
        #self.window_installed_snaps.add_child(self.builder, self.instd_lb_pane.vp)
        self.window_installed_snaps.add(self.instd_lb_pane.vp)
        # Not using "show_all" because of hidden buttons noted above.
        self.window_installed_snaps.show()
        # Not using "show_all" here because of unused hidden labels.
        self.instd_lb_pane.vp.show()
        self.window_available_snaps.add(self.avail_lb_pane.vp)
        self.window_available_snaps.show_all()

        # Connect GUI signals to Handler class.
        self.builder.connect_signals(handler.Handler())
        """
        # Adjust GUI in case of found 'wasta-offline' folder.
        self.updatable_offline_list = util.get_offline_updatable_snaps(self.start_folder)
        if len(self.updatable_offline_list) > 0:
            select_offline_update_rows(self.start_folder, init=True)
        """

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if not options:
            # No command line args passed: run GUI.
            self.activate()
            return 0

        if 'version' in options:
            proc = subprocess.run(
                ['apt-cache', 'policy', 'wasta-snap-manager'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            print(proc.stdout.decode())
            print('snapd version: %s' % util.get_snapd_version())
            return 0

        # Verify execution with elevated privileges.
        if os.geteuid() != 0:
            print("wasta-snap-manager needs elevated privileges; e.g.:\n\n$ pkexec", __file__, "\n$ sudo", __file__)
            exit(1)

        # Set up logging.
        util.set_up_logging()
        util.log_snapd_version(util.get_snapd_version())
        util.log_installed_snaps(self.installed_snaps_list)

        # Give terminal guidance for tracking updates.
        print('\nHint: To view update progress, open a new terminal and type:')
        print('$ snap changes')
        print('The last item on the list will be the in-progress update.')
        print('Watch the progress of this particular change with:')
        print('$ snap watch [number]\n')

        # Run offline and then online updates, if indicated.
        for opt in options:
            if opt == 'snaps-dir':
                folder = options['snaps-dir']
                # Move snaps into arch-specific subfolders for multi-arch support.
                util.wasta_offline_snap_cleanup(folder)
                # Update snaps from wasta-offline folder.
                status = cmdline.update_offline(folder)
                if status != 0:
                    return status
            elif opt == 'online':
                status = cmdline.update_online()
        return status

    def select_offline_update_rows(self, source_folder, init=False):
        rows = self.rows
        # Determine if it's a wasta-offline folder.
        basename = Path(source_folder).name
        if init and basename != 'wasta-offline':
            # Intial run and no 'wasta-offline' folder found. Return empty dictionary.
            offline_dict = {}
            return offline_dict
        updatable_offline = self.updatable_offline_list
        if len(updatable_offline) > 0:
            self.listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
            for entry in updatable_offline:
                index = rows[entry['name']]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)
        return updatable_offline

    def select_online_update_rows(self):
        installed_snaps = self.installed_snaps_list
        rows = self.rows
        #if len(self.updatable_online_list) > 0:
        if len(self.updatable_online_dict.keys()) > 0:
            self.listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
            for snap in self.updatable_online_dict.keys():
                index = rows[snap]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)
                box_row = row.get_child()
                label_note = box_row.get_children()[2]
                bytes = self.updatable_online_dict[snap]
                size_str = util.convert_filesize(bytes)
                text = ' '.join(['<', size_str])
                label_note.set_text(text)
                label_note.show()

    def deselect_online_update_rows(self):
        installed_snaps = self.installed_snaps_list
        rows = self.rows
        #for snap in self.updatable_online_list:
        for snap in self.updatable_online_dict.keys():
            index = rows[snap]
            row = self.listbox_installed.get_row_at_index(index)
            self.listbox_installed.unselect_row(row)
        if len(self.updatable_offline_list) == 0:
            self.listbox_installed.set_selection_mode(Gtk.SelectionMode.NONE)

    def populate_listbox_installed(self, list_box, snaps_list):
        # Remove any existing rows.
        try:
            children = list_box.get_children()
            for c in children:
                list_box.remove(c)
        except AttributeError:
            pass

        rows = {}
        count = 0
        # Create dictionary of relevant info: icon, name, description, revision.
        contents_dict = {}
        for entry in snaps_list:
            name = entry['name']
            icon_path = util.get_snap_icon(name)
            contents_dict[entry['name']] = {
                'icon': icon_path,
                'name': name,
                'summary': entry['summary'],
                'revision': entry['revision'],
                'confinement': entry['confinement']
            }
        # Use this dictionary to build each listbox row.
        for snap in sorted(contents_dict.keys()):
            row = guiparts.InstalledSnapRow(contents_dict[snap])
            list_box.add(row)
            row.show()
            rows[snap] = count
            count += 1
        list_box.show()
        return rows

    def populate_listbox_available(self, list_box, snaps_list):
        rows = {}
        if len(snaps_list) == 0:
            #if len(self.updatable_online_list) == 0 and len(self.updatable_offline_list) == 0:
            if len(self.updatable_online_dict.keys()) == 0 and len(self.updatable_offline_list) == 0:
                self.listbox_installed.set_selection_mode(Gtk.SelectionMode.NONE)
            return rows
        if len(self.updatable_offline_list) > 0:
            self.listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
        # Create a dictionary of useful snap details.
        contents_dict = {}
        for entry in snaps_list:
            contents_dict[entry['name']] = entry['file_path']
        index = 0
        for snap in sorted(contents_dict.keys()):
            file = contents_dict[snap]
            details = util.get_offline_snap_details(file)
            summary = details['summary']
            row = guiparts.AvailableSnapRow(snap, summary)
            list_box.add(row)
            install_button = row.button_install_offline
            install_button.connect("clicked", handler.Handler().on_install_button_clicked, snap)
            rows[snap] = index
            index += 1
            row.show_all()
        list_box.show()
        return rows


app = WSMApp()
