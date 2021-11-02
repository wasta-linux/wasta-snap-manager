""" Functions that run in background threads. """
# All of these functions run inside of threads and use GLib to communicate back.

import gi
import logging
import subprocess

from pathlib import Path
from gi.repository import Gdk, GLib, Gtk
gi.require_version("Gtk", "3.0")

from wsm import snapd
from wsm import util
from wsm import wsmapp


def handle_button_online_source_toggled(button):
    is_activated = button.get_active()

    label = wsmapp.app.label_button_source_online
    grid = wsmapp.app.grid_source
    spinner = Gtk.Spinner(halign=Gtk.Align.START)
    spinner.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.19, 0.20, 0.23, 1.0))

    text = ''
    # Clear the label text if not empty.
    GLib.idle_add(label.set_text, text)
    if is_activated:
        #text = 'Checking the Snap Store...'
        #GLib.idle_add(wsmapp.app.label_button_source_online.set_text, text)
        GLib.idle_add(label.hide)
        GLib.idle_add(grid.attach, spinner, 2, 0, 1, 1)
        GLib.idle_add(spinner.show)
        GLib.idle_add(spinner.start)
        if util.snap_store_accessible():
            text = ''
            wsmapp.app.updatable_online_dict = util.get_snap_refresh_dict()
            # wsmapp.app.select_online_update_rows()
            GLib.idle_add(wsmapp.app.select_online_update_rows)
        else:
            text = 'No connection to the Snap Store.'
            # wsmapp.app.button_source_online.set_active(False)
            GLib.idle_add(wsmapp.app.button_source_online.set_active, False)
        GLib.idle_add(spinner.stop)
        GLib.idle_add(spinner.hide)
        GLib.idle_add(label.show)
    else:
        text = ''
        # wsmapp.app.deselect_online_update_rows()
        GLib.idle_add(wsmapp.app.deselect_online_update_rows)

    GLib.idle_add(label.set_text, text)
    return

def handle_button_update_snaps_clicked():
    obj_rows_selected = wsmapp.app.listbox_installed.get_selected_rows()
    updatables = wsmapp.app.updatable_offline_list
    for row in obj_rows_selected:
        listbox = row.get_parent()
        # child = box; children = icon, box_info, label_update_note
        box_row = row.get_child()
        box_children = box_row.get_children()
        label_update_note = box_children[2]
        # children = snap_name, description
        snap_name = box_children[1].get_children()[0].get_text()
        label_update_text = label_update_note.get_text()

        spinner = Gtk.Spinner(halign=Gtk.Align.START, valign=Gtk.Align.CENTER)
        spinner.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.19, 0.20, 0.23, 1.0))
        GLib.idle_add(box_row.pack_end, spinner, False, False, 5)
        GLib.idle_add(label_update_note.hide)
        GLib.idle_add(spinner.show)
        GLib.idle_add(spinner.start)

        update_snap_offline(snap_name, updatables)

        # Update from online source.
        #if snap_name in wsmapp.app.updatable_online_list:
        if snap_name in wsmapp.app.updatable_online_dict.keys():
            status = update_snap_online(snap_name)

        # Post-install.
        GLib.idle_add(spinner.stop)
        GLib.idle_add(spinner.hide)
        if status == 0:
            GLib.idle_add(listbox.unselect_row, row)
        #row.hide()

def handle_install_button_clicked(button, snap):
    logging.debug(f"Start of function: worker.handle_install_button_clicked")

    # Get widget pointers.
    width = button.get_allocated_width()
    box_row = button.get_parent()
    row = box_row.get_parent()
    listbox = wsmapp.app.listbox_installed

    # Adjust widgets.
    spinner = Gtk.Spinner(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    GLib.idle_add(spinner.override_color, Gtk.StateFlags.NORMAL, Gdk.RGBA(0.19, 0.20, 0.23, 1.0))
    GLib.idle_add(spinner.set_property, "width-request", width)
    GLib.idle_add(box_row.pack_end, spinner, False, True, 5)
    GLib.idle_add(button.hide)
    GLib.idle_add(spinner.show)
    GLib.idle_add(spinner.start)

    # Get snap and assert files.
    lst = wsmapp.app.installable_snaps_list
    # Use list comprehension to get "list" of the single matching item.
    file_paths = [i['file_path'] for i in lst if i['name'] == snap]
    file_path = Path(file_paths[0])

    # Read /meta/snap.yaml in snap file to get 'core' and 'prerequisites'.
    offline_snap_details = util.get_offline_snap_details(file_path)

    # Install 'core' and 'prerequisites', if necessary.
    ret = 0 # initialize return code list
    base = offline_snap_details.get('base')
    if not base:
        logging.error(f"Couldn't determine base snap. Aborting install/update.")
        return 1
    logging.debug(f"Snap base for {snap}: {base}")

    # Instantiate local snap class.
    snapctl = snapd.Snap()

    # Try to install base snap, if needed.
    if not util.snap_is_installed(base):
        logging.debug(f"Installing base snap: {base}")
        base_paths = [entry['file_path'] for entry in lst if entry['name'] == base]
        base_path = Path(base_paths[0])
        ret += install_snap_offline(base_path)
        if ret == 0:
            # TODO: Remove base from available list.
            # Re-populate installed snaps window.
            wsmapp.app.populate_listbox_installed(listbox, snapctl.list())
    try:
        # Try to install prerequisite snaps, if necessary.
        prereqs = offline_snap_details['prerequisites']
        for prereq in prereqs:
            if not util.snap_is_installed(prereq):
                prereq_paths = [entry['file_path'] for entry in lst if entry['name'] == prereq]
                prereq_path = Path(prereq_paths[0])
                ret += install_snap_offline(prereq_path)
                if ret == 0:
                    # TODO: if successful, remove prereq from available list.
                    # Re-populate installed snaps window.
                    wsmapp.app.populate_listbox_installed(listbox, snapctl.list())
    except KeyError: # no prerequisites
        pass

    # Install offline snap itself.
    logging.debug(f"Installing snap: {snap}")
    ret += install_snap_offline(file_path)
    logging.debug(f"Installation of {snap} terminated with status {ret}.")

    # Post-install.
    GLib.idle_add(spinner.stop)
    GLib.idle_add(spinner.hide)
    if ret == 0: # successful installation
        # Re-populate installed snaps window.
        logging.debug(f"Removing installed snap from available list.")
        GLib.idle_add(row.hide)
        wsmapp.app.populate_listbox_installed(listbox, snapctl.list())
    else: # failed installation
        GLib.idle_add(button.show)
    logging.debug(f"End of function: worker.handle_install_button_clicked")

def update_snap_offline(snap_name, updatables):
    offline_names = [i['name'] for i in updatables]
    if snap_name in offline_names:
        file_paths = [i['file_path'] for i in updatables if i['name'] == snap_name]
        file_path = Path(file_paths[0])
        status = install_snap_offline(file_path)
    else:
        status = 0
    return status

def update_snap_online(snap):
    logging.info(f'Updating (refreshing) {snap} online.')
    try:
        subprocess.run(
            ['pkexec', 'snap', 'refresh', snap],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return 0
    except Exception as e:
        logging.error(e)
        logging.error(subprocess.stdout, subprocess.stderr)
        return 13

def acknowledge_snap_assert(root_type, assert_file):
    name = assert_file.stem.split('_')[0]
    if not assert_file.is_file():
        logging.error(f'{assert_file} is missing.')
        logging.error(f'Try installing {name} from the Snap Store instead.')
        # TODO: Display message saying how to install it from the Snap Store.
        return 10
    try:
        logging.info(f'Acknowledging \"{assert_file}\"')
        subprocess.run(
            [root_type, 'snap', 'ack', assert_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
    except Exception as e:
        logging.error(e)
        logging.error(subprocess.stdout, subprocess.stderr)
        return 11
    return 0

def get_assert_file(snap_file):
    return snap_file.parent / f"{snap_file.stem}.assert"

def install_snap_offline(snap_file):
    # Read /meta/snap.yaml in snap file to get 'core' and 'prerequisites'.
    offline_snap_details = util.get_offline_snap_details(snap_file)
    if not offline_snap_details:
        return 1
    logging.debug(f"snap details: {offline_snap_details}")

    root_type = util.get_root_type()
    if not root_type:
        return 1
    logging.debug(f"root type: {root_type}")

    classic_flag = False
    confinement = offline_snap_details.get('confinement')
    if confinement == 'classic':
        classic_flag = True
    logging.debug(f"confinement for {snap_file}: {confinement}")

    a_status = acknowledge_snap_assert(root_type, get_assert_file(snap_file))
    if a_status != 0:
        return a_status

    cmd = [root_type, 'snap', 'install', str(snap_file)]
    msg = f"Installing/Updating \"{snap_file}\""
    if classic_flag:
        cmd.insert(-1, '--classic')
        msg += ' with --classic flag'

    logging.info(msg)
    logging.debug(f"command: {' '.join(cmd)}")
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        return 0
    except Exception as e:
        # What are the possible errors here?
        logging.error(e)
        logging.error(subprocess.stdout, subprocess.stderr)
        return 12

def install_offline_snap_and_prereqs(app, snap_name):
    if util.snap_is_installed(snap_name):
        return 0
    snap_file = util.get_snap_file_path(snap_name, app.cmd_opts['snaps-dir'])
    if not snap_file:
        return 10
    logging.debug(f"starting install process for: {snap_file}")
    details = util.get_offline_snap_details(snap_file)
    logging.debug(f"snap file details: {details}")

    # Install snapd, base, and prerequisites first.
    if not util.snap_is_installed('snapd'):
        snapd_snap_file = util.get_snap_file_path('snapd', app.cmd_opts['snaps-dir'])
        if not snapd_snap_file:
            return 10
        d_status = install_snap_offline(snapd_snap_file)
        if d_status != 0:
            return d_status

    base_snap = details.get('base')
    if not util.snap_is_installed(base_snap):
        base_snap_file = util.get_snap_file_path(base_snap, app.cmd_opts['snaps-dir'])
        if not base_snap_file:
            return 10
        b_status = install_snap_offline(base_snap_file)
        if b_status != 0:
            return b_status

    for p in details.get('prerequisites'):
        p_status = install_offline_snap_and_prereqs(app, p)
        if p_status != 0:
            return p_status

    status = install_snap_offline(snap_file)
    return status
