from __future__ import absolute_import
from openspending.tasks.celery import celery

from celery.utils.log import get_task_logger
log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def ping():
    log.info("Pong.")


@celery.task(ignore_result=True)
def clean_sessions():
    import os
    import subprocess
    from pylons import config

    cache_dir = config.get('pylons.cache_dir')

    if cache_dir is None:
        log.warn(
            "No 'cache_dir' found in pylons config," +
            "unable to clean session files!")
        return

    sessions_dir = os.path.join(cache_dir, 'sessions')
    if not os.path.isdir(sessions_dir):
        log.warn(
            "No 'sessions' directory found in %s," +
            "skipping clean_sessions task!",
            cache_dir)
        return

    # remove all session files with an atime more than 1 day ago
    return subprocess.call(
        ['find', sessions_dir, '-type', 'f', '!', '-atime', '0', '-delete'])
