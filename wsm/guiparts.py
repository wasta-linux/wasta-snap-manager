""" Configure runtime GUI elements. """
# Gather info about installed and available snaps to generate lists.

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GdkPixbuf


class InstalledSnapRow(Gtk.ListBoxRow):
    def __init__(self, data):
        super(Gtk.ListBoxRow, self).__init__()
        self.data = data

        # Parse the input data.
        icon = data['icon']
        snap = data['name']
        description = data['summary']
        rev_installed = data['revision']
        rev_available = 'N/A'
        note = 'rev. ' + rev_installed + ' < ' + rev_available
        flag = data['confinement']

        # Define the row.
        self.box_row = Gtk.Box(orientation='horizontal')
        self.add(self.box_row)

        # Define the various parts of the row box.
        image = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=icon,
            width=32,
            height=32,
            preserve_aspect_ratio=True
        )
        self.label_icon = Gtk.Image.new_from_pixbuf(image)
        self.box_info = Gtk.Box(orientation='vertical')
        #label_rev_installed = Gtk.Label(rev_installed)
        #label_rev_available = Gtk.Label(rev_available)
        self.label_update_note = Gtk.Label(note)

        # Pack the various parts of the row box.
        self.box_row.pack_start(self.label_icon, False, False, 5)
        self.box_row.pack_start(self.box_info, False, False, 5)
        #box_row.pack_end(label_rev_installed, False, False, 5)
        #box_row.pack_end(label_rev_available, False, False, 5)
        self.box_row.pack_end(self.label_update_note, False, False, 5)

        # Define the 2 parts of the info box within the row.
        self.label_name = Gtk.Label(snap)
        self.label_name.set_alignment(0.0, 0.5)
        self.label_name.set_markup("<span weight=\"bold\">" + snap + "</span>")
        self.label_description = Gtk.Label(description)
        self.label_description.set_alignment(0.0, 0.5)
        self.label_description.set_ellipsize(Pango.EllipsizeMode.END)
        self.label_description.set_max_width_chars(60)

        # Pack the 2 parts of the info box into the row box.
        self.box_info.pack_start(self.label_name, False, False, 1)
        self.box_info.pack_start(self.label_description, False, False, 1)
        self.show_all()
        self.label_update_note.hide()

class AvailableSnapRow(Gtk.ListBoxRow):
    def __init__(self, snap, summary):
        super(Gtk.ListBoxRow, self).__init__()

        # Define the row.
        box_row = Gtk.Box(orientation='horizontal')
        self.add(box_row)

        # Define the various parts of the row box.
        box_info = Gtk.Box(orientation='vertical')
        box_info.set_property('margin-top', 1)
        box_info.set_property('margin-bottom', 1)
        self.button_install_offline = Gtk.Button()
        self.button_install_offline.set_property('margin-top', 6)
        self.button_install_offline.set_property('margin-bottom', 6)
        self.button_install_offline.set_label('Install')

        # Pack the various parts of the row box.
        box_row.pack_start(box_info, False, False, 10)
        box_row.pack_end(self.button_install_offline, False, False, 10)

        # Define the 2 parts of the info box within the row.
        label_name = Gtk.Label(snap)
        label_name.set_alignment(0.0, 0.5)
        label_name.set_markup("<span weight=\"bold\">" + snap + "</span>")
        label_summary = Gtk.Label(summary)
        label_summary.set_alignment(0.0, 0.5)
        label_summary.set_ellipsize(Pango.EllipsizeMode.END)
        label_summary.set_max_width_chars(60)

        # Pack the 2 parts of the info box into the row box.
        box_info.pack_start(label_name, False, False, 1)
        box_info.pack_start(label_summary, False, False, 1)
