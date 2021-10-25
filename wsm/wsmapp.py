""" Main GUI module. """

import gi
import logging
import os
import subprocess
import threading

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
from wsm import worker
from wsm import wsmwindow


class WSMApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id='org.wasta.apps.wasta-snap-manager',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
        )

        self.add_main_option(
            'debug', ord('d'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
            "Set log level to DEBUG", None
        )
        self.add_main_option(
            'online', ord('i'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
            'Update snaps from the online Snap Store.', None
        )
        self.add_main_option(
            'snaps-dir', ord('s'), GLib.OptionFlags.NONE, GLib.OptionArg.STRING,
            'Update snaps from offline folder.', '/path/to/wasta-offline'
        )
        self.add_main_option(
            'version', ord('V'), GLib.OptionFlags.NONE, GLib.OptionArg.NONE,
            'Print snapd version number.', None
        )

        # Get UI location based on current file location.
        self.ui_dir = '/usr/share/wasta-snap-manager/ui'
        if str(current_file_path.parents[1]) != '/usr/share/wasta-snap-manager':
            self.ui_dir = str(current_file_path.parents[1] / 'data' / 'ui')

        # Define app-wide variables.
        snapctl = snapd.Snap()
        self.runmode = ''
        self.installed_snaps_list = snapctl.list()
        self.installable_snaps_list = []
        self.updatable_offline_list = []
        self.updatable_online_dict = {}
        self.icon_theme = Gtk.IconTheme.get_default()
        themed_icon = self.icon_theme.lookup_icon('media-record', 48, 0)
        self.fallback_icon_path = themed_icon.get_filename()

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

    def do_command_line(self, command_line):
        self.cmd_args = command_line.get_arguments()
        self.cmd_opts = command_line.get_options_dict().end().unpack()
        self.log_level = logging.INFO

        if 'version' in self.cmd_opts:
            proc = subprocess.run(
                ['apt-cache', 'policy', 'wasta-snap-manager'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            print(proc.stdout.decode())
            print(f"snapd version: {util.get_snapd_version()}")
            return 0

        # Verify execution with elevated privileges.
        if os.geteuid() != 0:
            print("wasta-snap-manager needs elevated privileges; e.g.:\n\n$ pkexec", __file__, "\n$ sudo", __file__)
            exit(1)

        # Set loglevel.
        self.log_level = logging.INFO
        if 'debug' in self.cmd_opts:
            self.log_level = logging.DEBUG

        # Set up logging.
        util.set_up_logging(self.log_level)
        util.log_snapd_version(util.get_snapd_version())
        util.log_installed_snaps(self.installed_snaps_list)

        if not self.cmd_opts and not self.cmd_args:
            # No command line args passed: run GUI.
            self.activate()
            return 0

        # Give terminal guidance for tracking updates.
        print('\nHint: To view update progress, open a new terminal and type:')
        print('snap changes')
        print('The last item on the list will be the in-progress update.')
        print('Watch the progress of this particular change with:')
        print('snap watch [number]\n')

        # Run offline and then online updates, if indicated.
        #   TODO: Needs testing.
        status = 0
        early_return = False
        if 'snaps-dir' in self.cmd_opts:
            # Check for passed snap names to install.
            if len(self.cmd_args) > 1:
                install_list = self.cmd_args[1:]
                status = 0
                for s in install_list:
                    # Handle both snap name (i.e. search for file with given name), and
                    #   full snap file passed.
                    snap_file = util.get_snap_file_path(s, self.cmd_opts['snaps-dir'])
                    install_text = f"Installing {s}..."
                    print(install_text)
                    logging.info(install_text)
                    s_status = worker.install_offline_snap_and_prereqs(self, s)
                    # s_status = worker.install_snap_offline(snap_file)
                    if s_status != 0:
                        fail_text = f"\t{s} failed to install"
                        print(fail_text)
                        logging.error(fail_text)
                    status += s_status
                return status
            else:
                # Run offline updates, then continue.
                folder = self.cmd_opts['snaps-dir']
                # Move snaps into arch-specific subfolders for multi-arch support.
                util.wasta_offline_snap_cleanup(folder)
                # Update snaps from wasta-offline folder.
                status += cmdline.update_offline(folder)
                if status != 0:
                    return status
            early_return = True

        if 'online' in self.cmd_opts:
            # Run online updates, then exit.
            status = cmdline.update_online()
            return status

        # Return now if offline updates were done.
        if early_return:
            return status

        # Run GUI if other options were passed.
        self.activate()
        return status

    def do_activate(self):
        logging.debug(f"Start of function: app.do_activate")

        # Verify execution with elevated privileges.
        if os.geteuid() != 0:
            bin = '/usr/bin/wasta-snap-manager'
            print("wasta-snap-manager needs elevated privileges; e.g.:\n\n$ pkexec", bin, "\n$ sudo", bin)
            exit(1)

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
        logging.debug(f"End of function: app.do_activate")

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
        logging.debug(f"Start of function: populate_listbox_installed")

        # Check thread status.
        main_thread = True
        if threading.current_thread() != threading.main_thread():
            main_thread = False
        logging.debug(f"Function running in main thread?: {main_thread}")

        # Create dictionary of relevant info: icon, name, description, revision.
        contents_dict = util.snaps_list_to_dict(snaps_list, self)

        # Remove any existing rows.
        try:
            children = list_box.get_children()
            for c in children:
                if main_thread:
                    list_box.remove(c)
                else:
                    GLib.idle_add(list_box.remove, c)
        except AttributeError:
            pass

        # Build each new listbox row.
        rows = {}
        count = 0
        for snap in sorted(contents_dict.keys()):
            row = guiparts.InstalledSnapRow(contents_dict[snap])
            if main_thread:
                list_box.add(row)
                row.show()
            else:
                GLib.idle_add(list_box.add, row)
                GLib.idle_add(row.show)
            rows[snap] = count
            count += 1
        if main_thread:
            list_box.show()
        else:
            GLib.idle_add(list_box.show)
        logging.debug(f"End of function: populate_listbox_installed")
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
