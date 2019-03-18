from django.shortcuts import render
from django.http import HttpResponse
from .tasks import add


def index(request):
    # result = add.delay(2, 2)
    # print("CELERY TEST: ",result.get())
    return HttpResponse("Instâncias.")