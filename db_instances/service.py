from django.shortcuts import get_object_or_404
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from decouple import config

from .models import Credential


def adsync():

    db = get_object_or_404(Credential, name='MxGateway')

    domain_ldap_q = '''
        SELECT domain, address, user, `password`, base 
        FROM domain_adldap 
        WHERE domain = 'inova.net';
    '''

    domain_ldap_props_q = '''
        SELECT property_key 
        FROM domain_adldap_properties 
        WHERE domain = %s;
    '''

    accounts_props_q = '''
        SELECT eap.account, dlp.property_key, eap.property_name, eap.property_value  
        FROM email_accounts_properties as eap 
        INNER JOIN domain_adldap_properties as dlp ON eap.property_name = dlp.property_name 
        WHERE eap.domain_id = %s 
        AND eap.account = %s 
        GROUP BY eap.property_name;
    '''

    delete = '''
        DELETE FROM email_accounts_properties 
        WHERE account = %s 
        AND domain_id = %s AND property_value is NULL;
    '''

    create_or_update = '''
        INSERT INTO email_accounts_properties 
        VALUES (%(account)s, %(domain)s, %(name)s, %(value)s) 
        ON DUPLICATE KEY UPDATE 
        account = %(account)s, 
        domain_id = %(domain)s, 
        property_name = %(name)s, 
        property_value = %(value)s;
    '''

    get_property_name = '''
        SELECT property_name FROM domain_adldap_properties 
        WHERE domain = %s 
        AND property_key = %s 
        LIMIT 1;
    '''

    try:
        # connect to the database server
        cnx = mysql.connector.connect(user=db.user, password=db.password,
                                       host=db.host, database=db.database)

        print('\nConnect to dabase successful')

    except mysql.connector.Error as error:
        print(error)

    # execute the query
    cursor = cnx.cursor(buffered=True)

    cursor.execute(domain_ldap_q)
    domain_ldaps = cursor.fetchall()

    for (domain, address, user, password, base) in domain_ldaps:
        cursor.execute(domain_ldap_props_q, (domain,))
        domain_attr = cursor.fetchall()
        ldap_attr = []
        for (property_key,) in domain_attr:
            ldap_attr.append(property_key)

        print('LDAP DOMAIN ATT: ', ldap_attr)

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
            conn.search(
                BASE, '(mail=*)', attributes=ldap_attr)
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
                        cursor.execute(accounts_props_q,
                                       (domain_ldap, account))
                        accounts_ldaps = cursor.fetchall()

                        # check if mxGateway has account to be inserted or updated
                        if len(accounts_ldaps) > 0:
                            for item in entry['attributes']:
                                if len(entry['attributes'][item]) > 0:
                                    name = entry['attributes'][item]
                                    if isinstance(name, list):
                                        print('ATT.: ', item, ':', name[0])
                                        cursor.execute(get_property_name,(domain_ldap, item))
                                        name_mx = cursor.fetchone()
                                        print('ATT_MX.: ', item, ':', name_mx[0])
                                        data_l = {
                                            'account': account,
                                            'domain': domain_ldap,
                                            'name': name_mx[0],
                                            'value': name[0],
                                        }
                                        cursor.execute(create_or_update, data_l)
                                        # accept the change
                                        cnx.commit()
                                    else:
                                        print('ATT.: ', item, ':', name)
                                        cursor.execute(get_property_name,(domain_ldap, item))
                                        name_mx = cursor.fetchone()
                                        print('ATT_MX.: ', item, ':', name_mx[0])
                                        data_s = {
                                            'account': account,
                                            'domain': domain_ldap,
                                            'name': name_mx[0],
                                            'value': name,
                                        }
                                        cursor.execute(create_or_update, data_s)
                                        # accept the change
                                        cnx.commit()
                                else:
                                    print('ATT.: ', item, ': ', None)
                                    cursor.execute(get_property_name,(domain_ldap, item))
                                    name_mx = cursor.fetchone()
                                    print('ATT_MX.: ', item, ':', name_mx[0])
                                    data_n = {
                                        'account': account,
                                        'domain': domain_ldap,
                                        'name': name_mx[0],
                                        'value': None,
                                    }
                                    cursor.execute(create_or_update, data_n)
                                    # accept the change
                                    cnx.commit()

                            # cleans NULL values from database
                            cursor.execute(delete, (account, domain_ldap))
                            cnx.commit()

                            for (account, property_key, property_name, property_value) in accounts_ldaps:
                                print('ACCOUNT: ', account,
                                      ' - PROPERTY KEY: ', property_key,
                                      ' - PROPERTY NAME: ', property_name,
                                      ' - PROPERTY VALUE', property_value)
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

    cursor.close()
    cnx.close()
    ok = 'ok'
    return ok