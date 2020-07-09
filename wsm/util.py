""" Utility functions module. """

import gi
import logging
import os
import platform
import pwd
import re
import socket
import subprocess
import tempfile
import time
import urllib.request

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from pathlib import Path

from wsm import wsmapp
from wsm.snapd import snap


def get_user():
    try:
        # if using pkexec
        user = pwd.getpwuid(int(os.environ['PKEXEC_UID'])).pw_name
    except KeyError:
        # if using sudo
        user = pwd.getpwuid(os.geteuid()).pw_name
    return user

def set_up_logging():
    user = get_user()
    log_path = Path('/home', user, '.log', 'wasta-snap-manager')
    timestamp = time.strftime('%Y-%m-%d-%H-%M')
    hostname = socket.gethostname()
    log_file = timestamp + '-' + hostname + '.log'
    filename = Path(log_path, log_file)
    logging.basicConfig(
        filename=filename,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    logging.info('******* INSTALLING/UPDATING SNAPS **************')
    print('wasta-snap-manager log:')
    print(filename)

def log_installed_snaps(snaps):
    dct = {entry['name']: entry['revision'] for entry in snaps}
    logging.info('Installed snaps (revisions):')
    for k, v in dct.items():
        logging.info('\t%s (%s)' % (k, v))

def get_snapd_version():
    info = snap.system_info()
    version = info['version']
    return version

def log_snapd_version(version):
    logging.info('Snapd version: %s' % version)

def guess_offline_source_folder():
    user = get_user()
    logging.info('USER: %s' % user)
    begin = ''
    try:
        begin = sorted(Path('/media/' + user).glob('*/wasta-offline'))[0]
    except IndexError:
        try:
            # Check /mnt. How deep could it be, though?
            begin = sorted(Path('/mnt').glob('wasta-offline'))[0]
        except IndexError:
            try:
                # Check for VBox shared wasta-offline folder.
                begin = sorted(Path('/media/').glob('*/wasta-offline'))[0]
            except IndexError:
                # As a last resort just choose $HOME.
                alt_begin = Path('/home/' + user)
                logging.warning('No wasta-offline folder found. Falling back to \'%s\'.' % alt_begin)
    if begin:
        logging.info('wasta-offline folder found at \'%s\'' % begin)
    else:
        begin = alt_begin
    return user, begin.as_posix()

def get_snap_icon(snap):
    name = snap
    icon_path = ''
    fallback = '/usr/share/icons/HighContrast/48x48/actions/media-record.png'

    ### 1. Fastest location to try: ${SNAP}/meta/gui.
    snap_root = Path('/snap', name)
    subdirs = [s for s in snap_root.iterdir() if s.is_dir()]
    SNAP = sorted(subdirs, reverse=True)[0]
    gui_dir = Path(SNAP, 'meta', 'gui')
    suffixes = ['.png', '.svg']
    for s in suffixes:
        filename = Path(gui_dir, 'icon' + s)
        if filename.is_file():
            icon_path = filename
            return str(icon_path)

    ### 2. Next try file name from Gtk.IconTheme.
    icon_theme = Gtk.IconTheme.get_default()
    icon = icon_theme.lookup_icon(name, 48, 0)
    desktop_files = sorted(Path(SNAP).rglob('*' + name +'*.desktop'), reverse=True)
    desktop_file = desktop_files[0] if desktop_files else Path()
    if icon:
        icon_path = icon.get_filename()
        return str(icon_path)

    ### 3. Next try finding icon file name in any .desktop file.
    elif desktop_file.is_file():
        with open(desktop_file) as file:
            contents = file.read()
            icon_line = re.search('^Icon=.*$', contents, re.MULTILINE)
            if icon_line:
                icon_path = icon_line.group(0).split('=')[1]
                if icon_path.split('/')[0] == '${SNAP}':
                    # Relative path given.
                    icon_path = Path(str(SNAP) + icon_path[7:])
                    return str(icon_path)

    ### 4. Last resort: choose generic file.
    if not icon_path:
        icon_path = fallback

    return str(icon_path)

def get_snap_refresh_list():
    updatable = [s['name'] for s in snap.refresh_list()]
    return updatable

def add_item_to_update_list(item, update_list):
    # Convert list to 'set' type to eliminate duplicates.
    update_set = set(update_list)
    update_set.add(item)
    # Convert back to list before returning.
    update_list = list(update_set)
    return update_list

def get_list_from_snaps_folder(dir):
    list = []
    for assertfile in Path(dir).glob('*.assert'):
        # Each assert file is found first, then the corresponding snap file.
        snapfile = str(Path(dir, assertfile.stem + '.snap'))
        if Path(snapfile).exists():
            # The snap file is only included if both the assert and snap exist.
            snap, rev = Path(snapfile).stem.split('_')
            dictionary = {'name': snap, 'revision': rev, 'file_path': snapfile}
            list.append(dictionary)
    return list

def list_offline_snaps(dir, init=False):
    # Called at 2 different times:
    #   1. 'wasta-offline' found automatically; i.e. init=True
    #   2. User selects an arbitrary folder; i.e. init=False

    # Get basename of given dir.
    basename = Path(dir).name
    offline_list = []

    # Determine if it's a wasta-offline folder.
    if init and basename != 'wasta-offline':
        # Initial folder is user's home folder.
        return offline_list

    # Get arch in order to search correct wasta-offline folders.
    arch = platform.machine()
    if arch != 'x86_64':
        print("Arch", arch, "not supported yet for offline updates.")
        return offline_list
    else:
        arch = 'amd64'

    # Search the given directory for snaps.
    folders = ['.', 'all', arch]
    for folder in folders:
        if basename != 'wasta-offline':
            # An arbitrary folder is selected by the user.
            folder_path = Path(dir, folder)
        else:
            # A 'wasta-offline' folder is being used.
            folder_path = Path(dir, 'local-cache', 'snaps', folder)
        if folder_path.exists():
            # Add new dictionary from folder to existing one.
            #offline_dict.update(get_dict_from_snaps_folder(folder_path))
            #print(folder_path)
            offline_list += get_list_from_snaps_folder(folder_path)
    return offline_list

def get_offline_updatable_snaps(folder):
    offline_snaps_list = list_offline_snaps(folder)
    installed_snaps_list = wsmapp.app.installed_snaps_list
    # This is a list of snap dictionaries (name, revision, file_path).
    updatable_snaps_list = []
    for offl in offline_snaps_list:
        for inst in installed_snaps_list:
            if offl['name'] == inst['name'] and int(offl['revision']) > int(inst['revision']):
                updatable_snaps_list.append(offl)
    return updatable_snaps_list

def get_offline_installable_snaps(snaps_folder):
    # Include this offline folder in update sources list.
    rows = wsmapp.app.rows
    installed_snaps_list = wsmapp.app.installed_snaps_list
    offline_snaps_list = list_offline_snaps(snaps_folder)
    copy1 = copy2 = offline_snaps_list
    # Remove older revisions of each snap from offline_snaps_list.
    for e1 in copy1:
        for e2 in copy2:
            if e1['name'] == e2['name']:
                if int(e1['revision']) < int(e2['revision']):
                    offline_snaps_list.remove(e1)
                elif int(e2['revision']) < int(e1['revision']):
                    offline_snaps_list.remove(e2)

    # Make list of installable snaps.
    installable_snaps_list = []
    inst_names = [i['name'] for i in installed_snaps_list]
    for item in offline_snaps_list:
        if item['name'] not in inst_names:
            installable_snaps_list.append(item)
    return installable_snaps_list

def snap_store_accessible():
    try:
        urllib.request.urlopen('https://api.snapcraft.io', data=None, timeout=3)
        return True
    except:
        return False

def cat_yaml(snapfile):
    # Data needed: 'base', 'confinement', 'prerequisites'
    yaml = 'meta/snap.yaml'
    DEVNULL = open(os.devnull, 'w')
    with tempfile.TemporaryDirectory() as dest:
        subprocess.run(
            ['unsquashfs', '-n',  '-force', '-dest', dest, snapfile, '/' + yaml],
            stdout=DEVNULL
        )
        with open(Path(dest, yaml)) as file:
            return file.read()

def get_offline_snap_details(snapfile):
    contents = cat_yaml(snapfile).splitlines()
    p = Path(snapfile)
    name, revision = p.stem.split('_')
    output_dict = {'name': name}
    output_dict['revision'] = revision
    output_dict['base'] = 'core' # overwritten if 'base' specified in yaml
    for line in contents:
        if re.match('.*base\:.*', line):
            output_dict['base'] = line.split(':')[1].strip()
        elif re.match('.*confinement\:.*', line):
            output_dict['confinement'] = line.split(':')[1].strip()
        elif re.match('.*default\-provider\:.*', line):
            # TODO: It might be possible to have > 1 default-providers!
            output_dict['prerequisites'] = line.split(':')[1].strip()
        elif re.match('.*summary\:.*', line):
            output_dict['summary'] = line.split(':')[1].strip()
        else:
            continue
    return output_dict

def snap_is_installed(snap_name):
    response = snap.info(snap_name)
    try:
        if response['name'] == snap_name:
            return True
        else: # maybe not possible?
            return False
    except KeyError:
        return False
