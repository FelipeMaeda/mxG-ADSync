from django.shortcuts import render
from .tasks import adsync_task


def index(request):
    data = {
        'db_name': 'MxGateway',
        'from_domain': 'inova.net',
    }
    adsync_task.delay('MxGateway', 'inova.net')
    return render(request, 'db_instances/index.html')
