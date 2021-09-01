""" Utility functions module. """

import gi
import logging
import os
import platform
import pwd
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from pathlib import Path

from wsm import wsmapp
from wsm import snapd
snapctl = snapd.Snap()


def wasta_offline_snap_cleanup(folder):
    logging.info('Ensuring that snap packages are sorted into arch-specific subfolders.')
    snaps_dir = Path(folder, 'local-cache', 'snaps')
    snaps = get_list_from_snaps_folder(snaps_dir)
    if len(snaps) == 0:
        # Snaps folder contains no snaps. Return silently.
        return

    # Gather architecture info from snaps.
    #   Create dictionary of: {name_rev: [arch1, arch2, archN], ...}
    #       Valid arches: s390x, ppc64el, arm64, armhf, amd64, i386, all
    #           https://snapcraft.io/docs/architectures
    #       A snap could possibly run on multiple arch's without specifying "all".
    #         So, I suppose in that case the snap would need to be copied multiple
    #          times: once into each relevant arch folder!
    wayward_snaps = {}
    for snap_dict in snaps:
        file_path = snap_dict['file_path']
        contents = cat_yaml(file_path).splitlines()
        p = Path(file_path)
        name, revision = p.stem.split('_')
        wayward_snaps[p.stem] = []
        found = 0
        for line in contents:
            if found == 0:
                if re.match('.*architectures\:.*', line):
                    found = 1
            elif found == 1:
                if re.match('^\s*-\s.*', line):
                    wayward_snaps[p.stem].append(line.split()[1].strip())
                else:
                    # No more arches listed.
                    break

    # Move snaps to arch-specific subfolders.
    user = get_user()
    for snap_rev in wayward_snaps.keys():
        for arch in wayward_snaps[snap_rev]:
            # Create arch-specific subfolder(s).
            arch_dir = Path(snaps_dir, arch)
            if not arch_dir.is_dir():
                #os.mkdir(arch_dir, mode=777)
                Path.mkdir(arch_dir, mode=0o777)
                shutil.chown(arch_dir, user=user, group=user)
            # Copy snaps to arch-specific folder.
            assert_file = snap_rev + '.assert'
            snap_file = snap_rev + '.snap'
            logging.info('Moving {} and {} into {}'.format(snap_file, assert_file, arch_dir))
            try:
                shutil.move(str(Path(snaps_dir, snap_file)), str(arch_dir))
            except shutil.Error as err:
                logging.warning(err)
                continue
            shutil.move(str(Path(snaps_dir, assert_file)), str(arch_dir))
    print("Existing snap packages moved into relevant architecture subfolders.")

def get_user():
    root_type = get_root_type()
    user = None
    if root_type == 'pkexec':
        user = pwd.getpwuid(int(os.environ['PKEXEC_UID'])).pw_name
    elif root_type == 'sudo':
        user = pwd.getpwuid(int(os.environ['SUDO_UID'])).pw_name
    return user

def get_root_type():
    root_type = None
    if os.environ.get('PKEXEC_UID', None):
        root_type = 'pkexec'
    elif os.environ.get('SUDO_UID', None):
        root_type = 'sudo'
    return root_type

def set_up_logging(log_level):
    user = get_user()
    log_path = Path('/home', user, '.local', 'share', 'wasta-snap-manager')
    if not log_path.is_dir():
        os.mkdir(log_path)
    shutil.chown(log_path, user=user, group=user)
    timestamp = time.strftime('%Y-%m-%d-%H-%M')
    hostname = socket.gethostname()
    log_file = timestamp + '-' + hostname + '.log'
    filename = Path(log_path, log_file)
    logging.basicConfig(
        filename=filename,
        level=log_level,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    shutil.chown(filename, user=user, group=user)
    logging.info('******* INSTALLING/UPDATING SNAPS **************')
    print('wasta-snap-manager log:')
    print(filename)

def log_installed_snaps(snaps):
    dct = {entry['name']: entry['revision'] for entry in snaps}
    logging.info('Installed snaps (revisions):')
    for k, v in dct.items():
        logging.info('\t%s (%s)' % (k, v))

def get_snapd_version():
    info = snapctl.system_info()
    version = info['version']
    return version

def log_snapd_version(version):
    logging.info('Snapd version: %s' % version)

def guess_offline_source_folder():
    user = get_user()
    logging.info('username: %s' % user)
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
        # Move wasta-offline snaps into arch-specific subfolders for multi-arch support.
        wasta_offline_snap_cleanup(begin)
    else:
        begin = alt_begin
    return user, begin.as_posix()

def get_snap_icon(snap, app):
    name = snap
    logging.debug(f"snap name: {name}")
    icon_path = ''

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
            logging.debug(f"icon path: {icon_path}")
            return str(icon_path)

    ### 2. Next try file name from Gtk.IconTheme.
    app.icon_theme.append_search_path(str(Path(SNAP, 'usr', 'share', 'icons')))

    desktop_files = sorted(Path(SNAP).rglob('*' + name +'*.desktop'), reverse=True)
    desktop_file = desktop_files[0] if desktop_files else Path()
    if desktop_file.is_file():
        with open(desktop_file) as file:
            contents = file.read()
            icon_line = re.search('^Icon=.*$', contents, re.MULTILINE)
            if icon_line:
                icon_name = icon_line.group(0).split('=')[1]
                if icon_name.split('/')[0] == '${SNAP}':
                    # Relative path given.
                    icon_name = str(SNAP) + "/" + "/".join(icon_name.split('/')[1:])
                elif icon_name[0] == '/':
                    # Relative path given, but masquerading as absolute path.
                    icon_name = str(SNAP) + icon_name

                if Path(icon_name).is_file():
                    icon_path = icon_name
                elif app.icon_theme.lookup_icon(icon_name, 48, 0):
                    icon_path = app.icon_theme.lookup_icon(icon_name, 48, 0).get_filename()
                    logging.debug(f"icon path: {icon_path}")
                return str(icon_path)

    ### 3. Icon not found. Use fallback icon.
    logging.debug(f"Icon not found. Using fallback icon.")
    return str(app.fallback_icon_path)

def get_snap_refresh_list():
    # updatables = [s['name'] for s in snap.refresh_list()]
    updatables = [s['name'] for s in snapctl.refresh_list()]
    return updatables

def get_snap_refresh_dict():
    # updatables = {s['name']: s['download-size'] for s in snap.refresh_list()}
    updatables = {s['name']: s['download-size'] for s in snapctl.refresh_list()}
    return updatables

def add_item_to_update_list(item, update_list):
    # Convert list to 'set' type to eliminate duplicates.
    update_set = set(update_list)
    update_set.add(item)
    # Convert back to list before returning.
    update_list = list(update_set)
    return update_list

def get_list_from_snaps_folder(dir):
    snaps = []
    for assertfile in Path(dir).glob('*.assert'):
        # Each assert file is found first, then the corresponding snap file.
        snapfile = str(Path(dir, assertfile.stem + '.snap'))
        if Path(snapfile).exists():
            # The snap file is only included if both the assert and snap exist.
            snap, rev = Path(snapfile).stem.split('_')
            dictionary = {'name': snap, 'revision': rev, 'file_path': snapfile}
            snaps.append(dictionary)
    return snaps

def check_arch():
    # Get arch in order to search correct wasta-offline folders.
    arch = platform.machine()
    if arch != 'x86_64':
        label = Gtk.Label('{} architecture not yet supported for offline updates.'.format(arch))
        wsmapp.app.listbox_available.add(label)
        label.show()
    else:
        arch = 'amd64'
    return arch

def snaps_list_to_dict(snaps_list, fallback_icon_path):
    """Create dictionary of relevant info: icon, name, description, revision."""
    contents_dict = {}
    for entry in snaps_list:
        name = entry['name']
        icon_path = get_snap_icon(name, fallback_icon_path)
        contents_dict[name] = {
            'icon': icon_path,
            'name': name,
            'summary': entry['summary'],
            'revision': entry['revision'],
            'confinement': entry['confinement'],
        }
    return contents_dict

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
    # TODO: This could be passed as an argument.
    arch = platform.machine()
    if arch == 'x86_64':
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
    with open(os.devnull, 'w') as DEVNULL:
        with tempfile.TemporaryDirectory() as dest:
            subprocess.run(
                ['unsquashfs', '-n',  '-force', '-dest', dest, snapfile, '/' + yaml],
                stdout=DEVNULL
            )
            with open(Path(dest, yaml)) as f:
                #return f.read()
                contents = f.read()

    return contents

def get_offline_snap_details(snapfile):
    if not snapfile:
        return False
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
    # response = snap.info(snap_name)
    response = snapctl.info(snap_name)
    try:
        if response['name'] == snap_name:
            return True
        else: # maybe not possible?
            return False
    except KeyError:
        return False

def convert_filesize(input):
    B_amt = float(input)
    KB_amt = round(B_amt / 2**10)
    MB_amt = round(KB_amt / 2**10)
    if MB_amt > 1:
        output = ' '.join([str(MB_amt), 'MB'])
    elif KB_amt > 1:
        output = ' '.join([str(KB_amt), 'KB'])
    else:
        output = ' '.join([str(B_amt), 'B'])
    return output

def get_snap_file_path(snap, offline_base_path):
    # Search files in corect arch folder of offline_base_path for snap.
    arch = check_arch()
    wol_base_path = Path(offline_base_path) / 'local-cache' / 'snaps' / arch
    gen_base_path = Path(offline_base_path) / arch
    base_paths = [wol_base_path, gen_base_path]

    # Return full path of file matching snap.
    snap_path = False
    for p in base_paths:
        try:
            snap_path = sorted(p.glob(f'{snap}_*.snap'))[-1]
        except IndexError:
            continue

    if not snap_path:
        text = f"No matching file found for {snap}."
        # print(text)
        logging.error(text)
    else:
        logging.debug(f"{snap} found at {snap_path}")

    return snap_path
