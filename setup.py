# https://docs.python.org/3/distutils/setupscript.html

import glob
import re
from distutils.core import setup
from pathlib import Path


def get_vars():
    vars = {}

    # Get details from debian/* files.
    debian_dir = Path(__file__).parents[0] / 'debian'
    # Get version number from debian/changelog.
    changelog = debian_dir / 'changelog'
    with open(changelog) as f:
        first_line = f.readline()
    # 2nd term in 1st line; need to remove parentheses.
    vars['version'] = first_line.split()[1][1:-1]

    # Get contents of debian/control.
    control = debian_dir / 'control'
    with open(control) as f:
        text = f.read()
    # Get author and email.
    m = re.search('Maintainer:\s(.*)\n', text)
    contact = m.group(1).split('<')
    vars['author'] = contact[0].strip()
    vars['email'] = contact[1].strip().rstrip('>')
    # Get url.
    u = re.search('Homepage:\s(.*)\n', text)
    vars['url'] = u.group(1)
    # Get description.
    d = re.search('Description:\s(.*)\n', text)
    vars['description'] = d.group(1)
    return vars


vars = get_vars()


if __name__ == '__main__': # pragma: no cover
    setup(
        name='Wasta [Snap] Manager',
        version=vars.get('version'),
        description=vars.get('description'),
        author=vars.get('author'),
        author_email=vars.get('email'),
        url=vars.get('url'),
        packages=['wsm'],
        package_data={'wsm': ['README.md']},
        scripts=['bin/wasta-snap-manager'],
        data_files=[
            ('share/polkit-1/actions', glob.glob('data/actions/*')),
            ('share/icons/hicolor/scalable/apps', glob.glob('data/icons/*.svg')),
            ('share/wasta-snap-manager/ui', glob.glob('data/ui/*.glade')),
            ('share/applications', glob.glob('data/applications/*.desktop')),
        ]
    )
