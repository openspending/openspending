from __future__ import absolute_import
from openspending.tasks.celery import celery

from celery.utils.log import get_task_logger
log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def ping():
    log.info("Pong.")
