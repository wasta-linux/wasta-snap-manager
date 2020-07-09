""" Update snap packages from the command line. """

from os import path

from wsm import util
from wsm import worker

def update_offline(folder):
    folder = path.abspath(folder)
    updatables = util.get_offline_updatable_snaps(folder)
    snap_names = [i['name'] for i in updatables]
    status = 0
    for snap_name in snap_names:
        print('updating %s from %s...' % (snap_name, folder))
        substatus = worker.update_snap_offline(snap_name, updatables)
        status += substatus
    return 0

def update_online():
    snaps = util.get_snap_refresh_list()
    status = 0
    for snap in snaps:
        print('updating %s' % snap)
        substatus = worker.update_snap_online(snap)
        status += substatus
    return status
