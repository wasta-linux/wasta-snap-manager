""" Update snap packages from the command line. """

import logging
from os import path

from wsm import util
from wsm import worker

def update_offline(folder):
    folder = path.abspath(folder)
    updatables = util.get_offline_updatable_snaps(folder)
    snap_names = [i['name'] for i in updatables]
    status = 0
    for snap_name in snap_names:
        logging.info(f"updating {snap_name} from {folder}...")
        substatus = worker.update_snap_offline(snap_name, updatables)
        status += substatus
    return 0

def update_online():
    snaps = util.get_snap_refresh_dict()
    status = 0
    for snap in snaps.keys():
        logging.info(f"updating {snap}")
        substatus = worker.update_snap_online(snap)
        status += substatus
    return status
