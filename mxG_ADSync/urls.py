from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('credenciais/', include('db_instances.urls')),
    path('admin/', admin.site.urls),
]
