""" Main GUI module. """

import gi
import logging

from pathlib import Path
current_file_path = Path(__file__)

gi.require_version("Gtk", "3.0")
from gi.repository import Gio
from gi.repository import GLib
from gi.repository import Gtk

from wsm import cmdline
from wsm import handler
from wsm import guiparts
from wsm import util
from wsm import snapd


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
        self.updatable_online_list = []

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
        # Start GUI logging
        util.set_up_logging()
        util.log_snapd_version(util.get_snapd_version())
        util.log_installed_snaps(self.installed_snaps_list)

        # Define window and make runtime adjustments.
        # TODO: The window could be its own class in its own module.
        self.window = self.builder.get_object('window_snap_manager')
        self.add_window(self.window)
        self.window.show()

        # Hide label_can_update b/c it seems to be confusing, but saving just in case.
        self.label_can_update.hide()
        # Hide button_remove_snaps b/c it doesn't launch right when installed.
        self.button_remove_snaps.hide()

        # Make GUI initial adjustments.
        self.user, self.start_folder = util.guess_offline_source_folder()
        self.button_source_offline.set_current_folder(self.start_folder)

        # Add ListBox widgets.
        self.listbox_installed = Gtk.ListBox()
        self.listbox_installed.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox_installed.set_activate_on_single_click(True)

        self.listbox_available = Gtk.ListBox()
        self.listbox_available.set_selection_mode(Gtk.SelectionMode.NONE)

        # Add viewports for Installed & Available panes.
        self.wis_vp = Gtk.Viewport()
        self.wis_vp.add_child(self.builder, self.listbox_installed)
        self.window_installed_snaps.add_child(self.builder, self.wis_vp)
        self.rows = self.populate_listbox_installed(self.listbox_installed, self.installed_snaps_list)

        self.was_vp = Gtk.Viewport()
        self.was_vp.add_child(self.builder, self.listbox_available)
        self.window_available_snaps.add_child(self.builder, self.was_vp)
        self.window_installed_snaps.show()
        #self.window_available_snaps.show()
        self.wis_vp.show()

        # List populated later with self.populate_listbox_available().
        #   But initial entry added here for user guidance.
        self.av_row_init = Gtk.ListBoxRow()
        self.listbox_available.add(self.av_row_init)
        text = "<span style=\"italic\">Please select an offline folder above.</span>"
        self.label_av_row_init = Gtk.Label(text)
        self.label_av_row_init.set_property("use-markup", True)
        self.av_row_init.add(self.label_av_row_init)
        # I can't get this to show up, so doing it manually instead.
        #self.listbox_available.set_placeholder(self.av_row_init)
        self.was_vp.show_all()

        # Connect GUI signals to Handler class.
        self.hand = handler.Handler()
        self.builder.connect_signals(self.hand)

        # Adjust GUI in case of found 'wasta-offline' folder.
        self.updatable_offline_list = util.get_offline_updatable_snaps(self.start_folder)
        if len(self.updatable_offline_list) > 0:
            select_offline_update_rows(self.start_folder, init=True)
        self.installable_snaps_list = util.get_offline_installable_snaps(self.start_folder)
        if len(self.installable_snaps_list) > 0:
            # Remove any existing rows (placeholder, previous folder, etc.).
            children = self.listbox_available.get_children()
            for c in children:
                self.listbox_available.remove(c)
            self.populate_listbox_available(self.listbox_available, self.installable_snaps_list)

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if not options:
            # No command line args passed: run GUI.
            self.activate()
            return 0

        if 'version' in options:
            print('snapd version: %s' % util.get_snapd_version())
            return 0

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
        if len(self.updatable_online_list) > 0:
            self.listbox_installed.set_selection_mode(Gtk.SelectionMode.MULTIPLE)
            for snap in self.updatable_online_list:
                index = rows[snap]
                row = self.listbox_installed.get_row_at_index(index)
                self.listbox_installed.select_row(row)
                box_row = row.get_child()

    def deselect_online_update_rows(self):
        installed_snaps = self.installed_snaps_list
        rows = self.rows
        for snap in self.updatable_online_list:
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
            if len(self.updatable_online_list) == 0 and len(self.updatable_offline_list) == 0:
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
            install_button.connect("clicked", self.hand.on_install_button_clicked, snap)
            rows[snap] = index
            index += 1
            row.show_all()
        list_box.show()
        return rows


app = WSMApp()
