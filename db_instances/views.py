from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.template import loader
from .tasks import adsync_task
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from decouple import config
from .models import Credential


def index(request):
    dbs = Credential.objects.all()
    db_selected = request.GET.get('b')
    if db_selected != None:
        adsync_task.delay(db_selected)
    print('DB_ID: ', db_selected)
    return render(request, 'db_instances/index.html', {'dbs': dbs})