from __future__ import absolute_import, unicode_literals
from celery import shared_task
from .service import adsync


@shared_task
def adsync_task(db_id):
    return adsync(db_id)