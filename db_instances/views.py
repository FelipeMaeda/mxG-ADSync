from django.shortcuts import render
from django.http import HttpResponse
from .tasks import add
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector


def index(request):

    cnx = mysql.connector.connect(user='xxxxxxx', password='xxxxxxxxxxx',
                              host='xxxxx',
                              database='xxxxx')
    cnx.close()
    # result = add.delay()
    # print("CELERY TEST: ",result.get())
    # in mxhero DB domain_aldap TABLE address is SEVER
    # SERVER = 'inovmbox01.aws.inova.com.br'
    # USER = 'cn=inova.net,cn=users,dc=inovmbox01,dc=aws,dc=inova,dc=com,dc=br'
    # PASSWORD = 'e7eq_Y3pA_'
    # BASE='dc=inova,dc=net'

    # SERVER_DEMO = 'ipa.demo1.freeipa.org'
    # USER_DEMO = 'uid=admin,cn=users,cn=accounts,dc=demo1,dc=freeipa,dc=org'
    # PASSWORD_DEMO = 'Secret123'
    # BASE_DEMO = 'dc=demo1,dc=freeipa,dc=org'

    # total_entries = 0
    # server = Server(SERVER, get_info=ALL)
    # conn = Connection(server, USER, PASSWORD, auto_bind=True)
    # conn.search(BASE, '(displayName=*)', attributes=['displayName'])
    # total_entries += len(conn.response)
    # if total_entries > 0:
    #     for entry in conn.response:
    #         print('CHECK: ', entry['attributes'])
    # else:
    #     print('NO RESULTS')

    # conn.unbind()
    return HttpResponse("Instâncias.")
