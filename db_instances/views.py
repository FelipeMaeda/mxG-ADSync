from django.shortcuts import render
from django.http import HttpResponse
from .tasks import add
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from mysql.connector import errorcode
from decouple import config



def index(request):
    query1 = ("SELECT domain, address, user, `password`, base, directory_type "
              "FROM domain_adldap")
    query2 = ("SELECT account, property_name, property_value "
              "FROM email_accounts_properties "
              "WHERE account = %s")
    try:
        cnx = mysql.connector.connect(user='mxgateway', password='eipheiThohgai7IeQu5o',
                                      host='192.168.6.80', database='mxhero')
        print('Connect to dabase successful')

        cursor = cnx.cursor(buffered=True)
        cursor.execute(query1)
        first_q = cursor.fetchall()

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)


    for (domain, address, user, password, base, directory_type) in first_q:
        try:
            print('IN DOMAIN: ', domain)
            # in mxhero DB domain_aldap TABLE address is SEVER
            SERVER = address
            USER = user
            PASSWORD = password
            BASE = base
            total_entries = 0
            server = Server(SERVER, get_info=ALL)
            conn = Connection(server, USER, PASSWORD, auto_bind=True)
            conn.search(BASE, '(displayName=*)',
                        attributes=['givenName','initials', 'displayName', 'sn', 'telephoneNumber',
                        'homePhone', 'mobile', 'pager', 'facsimileTelephoneNumber', 'company',
                        'title', 'mail', 'street', 'l', 'st', 'postalCode', 'co', 'description', 
                        'zimbraNotes'])
            print('RESULT: ', conn.result)
            total_entries += len(conn.response)
            if total_entries > 0:
                for entry in conn.response:
                    emails = entry['attributes']['mail']
                    for email in emails: 
                        account = email.split("@")[0]
                        print('ACCOUNT NAME: ', account)
                        cursor.execute(query2, (account,))
                        second_q = cursor.fetchall()
                        for (account, property_name, property_value) in second_q:
                            print('ACCOUNT: ', account, ' - PROPERTY NAME: ',
                                  property_name, ' - PROPERTY VALUE: ', property_value)

            else:
                print('NO RESULTS FOR: ', domain)
            conn.unbind()
            print('####### NEXT #######')
        except Exception as e:
            print("ERROR: ", domain, ' - ', e)
    cnx.close()

    # result = add.delay()
    # print("CELERY TEST: ",result.get())

    return HttpResponse("Instâncias.")
