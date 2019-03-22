from django.shortcuts import render
from django.http import HttpResponse
from .tasks import add
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from mysql.connector import errorcode
from decouple import config


def index(request):
    try:
        cnx = mysql.connector.connect(user='', password='',
                                      host='', database='')
        print('Connect to dabase successful')

        cursor = cnx.cursor()
        query = ("SELECT domain, address, user, `password`, base, directory_type "
                 "FROM domain_adldap")
        cursor.execute(query)

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    for (domain, address, user, password, base, directory_type) in cursor:
        try:
            if directory_type == 'zimbra':
                print('DOMAIN: ', domain, ' -> ZIMBRA')
                # in mxhero DB domain_aldap TABLE address is SEVER
                SERVER = address
                USER = user
                PASSWORD = password
                BASE = base
                total_entries = 0
                server = Server(SERVER, get_info=ALL)
                conn = Connection(server, USER, PASSWORD, auto_bind=True)
                conn.search(BASE, '(displayName=*)',
                            attributes=['displayName', 'mail'])
                total_entries += len(conn.response)
                if total_entries > 0:
                    for entry in conn.response:
                        print('ATTRIBUTES: ', entry['attributes'])
                else:
                    print('NO RESULTS FOR: ', domain)
                conn.unbind()
                print('####### NEXT #######')
            else:
                print('DOMAIN', domain, ' -> NOT ZIMBRA')
        except:
            pass
    cnx.close()

    # result = add.delay()
    # print("CELERY TEST: ",result.get())

    return HttpResponse("Instâncias.")
