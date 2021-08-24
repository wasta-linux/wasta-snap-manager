""" Window classes """

import gi
import logging

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from wsm import util


class InstalledListBoxPane(Gtk.Viewport):
    def __init__(self, app):
        logging.debug(f"Start of function: __init__ of InstalledListBoxPane")
        # Add ListBox widgets.
        app.listbox_installed = Gtk.ListBox()
        app.listbox_installed.set_selection_mode(Gtk.SelectionMode.NONE)
        app.listbox_installed.set_activate_on_single_click(True)

        # Add ListBox to Viewport.
        self.vp = Gtk.Viewport()
        self.vp.add(app.listbox_installed)

        app.rows = app.populate_listbox_installed(app.listbox_installed, app.installed_snaps_list)

        # Select updatable snaps in case of found 'wasta-offline' folder.
        app.updatable_offline_list = util.get_offline_updatable_snaps(app.start_folder)
        if len(app.updatable_offline_list) > 0:
            app.select_offline_update_rows(app.start_folder, init=True)
        logging.debug(f"End of function: __init__ of InstalledListBoxPane")

class AvailableListBoxPane():
    def __init__(self, app):
        logging.debug(f"Start of function: __init__ of AvailableListBoxPane")
        # Add ListBox widget.
        app.listbox_available = Gtk.ListBox()
        app.listbox_available.set_selection_mode(Gtk.SelectionMode.NONE)

        # Add ListBox to Viewport.
        self.vp = Gtk.Viewport()
        self.vp.add(app.listbox_available)

        # List populated later with self.populate_listbox_available().
        #   But initial entry added here for user guidance.
        row_init = Gtk.ListBoxRow()
        app.listbox_available.add(row_init)
        text = "<span style=\"italic\">Please select an offline folder above.</span>"
        label_row_init = Gtk.Label(text)
        label_row_init.set_property("use-markup", True)
        row_init.add(label_row_init)

        # I can't get this to show up, so I did it manually instead.
        #app.listbox_available.set_placeholder(row_init)

        app.installable_snaps_list = util.get_offline_installable_snaps(app.start_folder)
        if len(app.installable_snaps_list) > 0:
            # Remove any existing rows (placeholder, previous folder, etc.).
            children = app.listbox_available.get_children()
            for c in children:
                app.listbox_available.remove(c)
            app.populate_listbox_available(app.listbox_available, app.installable_snaps_list)
        logging.debug(f"End of function: __init__ of AvailableListBoxPane")
