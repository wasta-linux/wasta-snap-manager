import os
import re
import subprocess
import tempfile

from pathlib import Path

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
    #print(cat_yaml(snapfile))
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
            output_dict['prerequisites'] = line.split(':')[1].strip()
        else:
            continue
    print(output_dict)
    return output_dict

def snap_is_installed(snap_name):
    print(snap.info(snap_name))

snap_is_installed('chromium')
