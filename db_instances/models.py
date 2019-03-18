from django.db import models

# Create your models here.

class Credential(models.Model):
    name = models.CharField(max_length=20, default='MxGateway')
    host = models.CharField(max_length=100, default='192.168.6.80:3306' )
    user = models.CharField(max_length=20, default='mxgateway')
    password = models.CharField(max_length=20, default='xxxxxx')
    database = models.CharField(max_length=20, default='mxhero')

    def __str__(self):
        return self.name
