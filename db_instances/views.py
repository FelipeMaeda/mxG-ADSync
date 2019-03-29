from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .tasks import adsync_task
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from decouple import config

from .models import Credential


def index(request):
    adsync_task.delay()
    return HttpResponse("LDAP SYNC COMPLETE.")