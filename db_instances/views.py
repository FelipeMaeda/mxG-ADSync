from django.shortcuts import get_object_or_404, render
from .tasks import adsync_task
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from .models import Credential
from dateutil.parser import parse

import json


def index(request):
    dbs = Credential.objects.all()
    created_tasks = PeriodicTask.objects.exclude(name='celery.backend_cleanup')
    total_tasks = len(created_tasks)
    if request.method == "POST":
        db_selected = request.POST.get('id')
        start = request.POST.get('start')
        dt = parse(start)
        interval = request.POST.get('interval')
        task_name = request.POST.get('task_name')

        print("DB_ID: ", db_selected)
        print('NAME: ', task_name)
        print('START: ', dt)
        print('INTERVAL: ', interval)

        schedule, created = IntervalSchedule.objects.get_or_create(every=interval,
                                                                   period=IntervalSchedule.MINUTES,)

        PeriodicTask.objects.create(interval=schedule,
                                    name=task_name,
                                    task='db_instances.tasks.adsync_task',
                                    args=json.dumps([db_selected]),
                                    start_time=dt)

        created_tasks = PeriodicTask.objects.exclude(name='celery.backend_cleanup')
        total_tasks = len(created_tasks)

    if request.method == "GET" and request.GET.get('tarefa') != None:
        print('TAREFA :' , request.GET.get('ativada'))
        task = PeriodicTask.objects.get(name=request.GET.get('tarefa'))
        print('TASK: ', task)
        task.enabled = request.GET.get('ativada')
        task.save()
        created_tasks = PeriodicTask.objects.exclude(name='celery.backend_cleanup')
        total_tasks = len(created_tasks)

    db_selected = None
    start = None
    interval = None
    return render(request, 'db_instances/index.html', { 'dbs': dbs, 'created_tasks': created_tasks, 'total_tasks':total_tasks })
