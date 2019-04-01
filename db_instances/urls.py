from django.urls import path

from . import views

app_name = 'db_instances'

urlpatterns = [
    path('', views.index, name='index'),
]