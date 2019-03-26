from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from .tasks import add
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from mysql.connector import errorcode
from decouple import config

from .models import Credential


def index(request):
    db = get_object_or_404(Credential, name='MxGateway')

    domain_ldap_q = '''
                SELECT domain, address, user, `password`, base, directory_type 
                FROM domain_adldap
            '''

    domain_ldap_props_q = '''
                SELECT property_key 
                FROM domain_adldap_properties 
                WHERE domain = %s
            '''

    accounts_props_q = '''
                SELECT account, property_name, property_value 
                FROM email_accounts_properties 
                WHERE account = %s 
                AND domain_id = %s
            '''

    try:
        cnx = mysql.connector.connect(user=db.user, password=db.password,
                                      host=db.host, database=db.database)
        print('\nConnect to dabase successful')

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)

    cursor = cnx.cursor(buffered=True)
    cursor.execute(domain_ldap_q)
    domain_ldaps = cursor.fetchall()

    for (domain, address, user, password, base, directory_type) in domain_ldaps:
        cursor.execute(domain_ldap_props_q, (domain,))
        domain_attr = cursor.fetchall()
        attr = []
        for (property_key) in domain_attr:
            attr += property_key
        try:
            print('\nIN DOMAIN: ', domain)
            # in mxhero DB domain_aldap TABLE address is SEVER
            SERVER = address
            USER = user
            PASSWORD = password
            BASE = base
            total_entries = 0
            server = Server(SERVER, get_info=ALL)
            conn = Connection(server, USER, PASSWORD, auto_bind=True)
            conn.search(BASE, '(mail=*)', attributes=attr)
            print('RESULT: ', conn.result)
            total_entries += len(conn.response)

            if total_entries > 0:
                for entry in conn.response:
                    emails = entry['attributes']['mail']
                    for email in emails:
                        account = email.split("@")[0]
                        domain_ldap = email.split("@")[1]
                        print('DOMAIN NAME: ', domain_ldap)
                        print('ACCOUNT NAME: ', account)
                        print('LDAP ATTRIBUTES: ', entry['attributes'])
                        cursor.execute(accounts_props_q, (account, domain_ldap))
                        accounts_ldaps = cursor.fetchall()
                        if len(accounts_ldaps) > 0:
                            for (account, property_name, property_value) in accounts_ldaps:
                                print('PROPERTY NAME: ',
                                      property_name, ' - PROPERTY VALUE: ', property_value)
                        else:
                            print('MXGATEWAY PROPERTIES: NO RESULTS')
                    print('\n')

            else:
                print('NO ENTRIES FOR: ', domain)
            print('TOTAL: ', len(conn.response))
            conn.unbind()
            print('########## END OF DOMAIN ##########')
        except Exception as e:
            print("ERROR: ", domain, ' - ', e)
    cnx.close()

    # result = add.delay()
    # print("CELERY TEST: ",result.get())

    return HttpResponse("Instâncias.")
