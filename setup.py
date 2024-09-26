# https://docs.python.org/3/distutils/setupscript.html

import glob
import re
from distutils.core import setup
from pathlib import Path


def get_version():
    version = '0.0.0'
    wsm_init = Path(__file__).parent / 'wsm' / '__init__.py'
    with wsm_init.open() as f:
        for line in f:
            if line.startswith('__version__'):
                version = line.split('=')[1].strip().strip("'")
    return version


def get_vars():
    vars = {}

    # Get version number.
    vars['version'] = get_version()

    # Get details from debian/* files.
    debian_dir = Path(__file__).parents[0] / 'debian'
    # Get contents of debian/control.
    control = debian_dir / 'control'
    with open(control) as f:
        text = f.read()
    # Get author and email.
    m = re.search(r'Maintainer:\s(.*)\n', text)
    contact = m.group(1).split('<')
    vars['author'] = contact[0].strip()
    vars['email'] = contact[1].strip().rstrip('>')
    # Get url.
    u = re.search(r'Homepage:\s(.*)\n', text)
    vars['url'] = u.group(1)
    # Get description.
    d = re.search(r'Description:\s(.*)\n', text)
    vars['description'] = d.group(1)
    return vars


vars = get_vars()


if __name__ == '__main__':  # pragma: no cover
    setup(
        name='Wasta [Snap] Manager',
        version=vars.get('version'),
        description=vars.get('description'),
        author=vars.get('author'),
        author_email=vars.get('email'),
        url=vars.get('url'),
        packages=['wsm'],
        package_data={'wsm': ['README.md']},
        scripts=['scripts/wasta-snap-manager'],
        data_files=[
            ('share/polkit-1/actions', glob.glob('data/actions/*')),
            ('share/icons/hicolor/scalable/apps', glob.glob('data/icons/*.svg')),  # noqa: E501
            ('share/wasta-snap-manager/ui', glob.glob('data/ui/*.glade')),
            ('share/applications', glob.glob('data/applications/*.desktop')),
        ]
    )
