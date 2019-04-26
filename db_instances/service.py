from django.shortcuts import get_object_or_404
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from decouple import config
import datetime
from .models import Credential


def adsync(db_name, from_domain):

    db = get_object_or_404(Credential, name=db_name)
    print('DB: ', db)

    domain_ldap_q = '''
        SELECT domain, address, user, `password`, base 
        FROM domain_adldap 
        WHERE domain = %s;
    '''

    search_account = '''
        SELECT account 
        FROM email_accounts_properties 
        WHERE domain_id = %s 
        AND account = %s;
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

    delete = '''
        DELETE FROM email_accounts_properties 
        WHERE property_value is NULL;
    '''

    properties_mx_name = '''
        SELECT property_name FROM domain_adldap_properties 
        WHERE property_key = %s 
        GROUP BY property_name;
    '''

    ldap_attrs = [
        'street',
        'l',
        'company',
        'co',
        'description',
        'displayName',
        'mail',
        'facsimileTelephoneNumber',
        'givenName',
        'homePhone',
        'initials',
        'title',
        'sn',
        'mobile',
        'zimbraNotes',
        'pager',
        'postalCode',
        'st',
        'telephoneNumber']

    try:
        # connect to the database server
        cnx = mysql.connector.connect(user=db.user, password=db.password,
                                      host=db.host, database=db.database)

        print('\nConnect to dabase successful')

    except mysql.connector.Error as error:
        print(error)

    # get ldap domain properties
    cursor = cnx.cursor(buffered=True)
    cursor.execute(domain_ldap_q, (from_domain,))
    domain_ldaps = cursor.fetchall()

    # connect to specific ldap domain
    for (domain, address, user, password, base) in domain_ldaps:
        try:
            print('\nIN DOMAIN: ', domain)
            SERVER = address
            USER = user
            PASSWORD = password
            BASE = base
            total_entries = 0
            server = Server(SERVER, get_info=ALL)
            conn = Connection(server, USER, PASSWORD, auto_bind=True)
            # Set filters in searching ldpa
            conn.search(
                BASE, '(mail=*)', attributes=ldap_attrs)

            total_entries += len(conn.response)

            if total_entries > 0:
                accounts_to_add = (domain,)
                for entry in range(total_entries):
                    emails = conn.response[entry]['attributes']['mail']
                    for email in emails:
                        account = email.split("@")[0]
                        domain_ldap = email.split("@")[1]
                        # print('ACCOUNT: ', account)
                        cursor.execute(search_account, (domain_ldap, account))
                        has_account = cursor.fetchone()
                        if has_account is None:
                            date_time = datetime.datetime.now()
                            data_source = 'adladp'
                            group_name = None
                            is_mail_list = 0
                            accounts_to_add += (account, date_time, date_time, data_source, group_name, is_mail_list)
                        try:
                            for ldap_attr in ldap_attrs:
                                print('LDAP ATT: ', ldap_attr)
                                cursor.execute(
                                    properties_mx_name, (ldap_attr,))
                                mx_prop = cursor.fetchone()
                                curr_item = conn.response[entry]['attributes'][ldap_attr]
                                # check if a especifc ldap attribute value is empty
                                if len(curr_item) > 0:
                                    print('CURR: ', curr_item)
                                    if isinstance(curr_item, list):
                                        data_l = {
                                            'account': account,
                                            'domain': domain_ldap,
                                            'name': mx_prop[0],
                                            'value': curr_item[0],
                                        }
                                        print('DATA: ', data_l)
                                        cursor.execute(
                                            create_or_update, data_l)
                                        # accept the change
                                        cnx.commit()
                                    else:
                                        data_s = {
                                            'account': account,
                                            'domain': domain_ldap,
                                            'name': mx_prop[0],
                                            'value': curr_item,
                                        }
                                        print('DATA: ', data_s)
                                        cursor.execute(
                                            create_or_update, data_s)
                                        # accept the change
                                        cnx.commit()
                                else:
                                    data_n = {
                                        'account': account,
                                        'domain': domain_ldap,
                                        'name': mx_prop[0],
                                        'value': None,
                                    }
                                    print('DATA: ', data_n)
                                    cursor.execute(create_or_update, data_n)
                                    # accept the change
                                    cnx.commit()
                        except Exception as inst:
                            # by passes create or update mysql method when there is no specific account
                            # to especific domain in a database
                            print('ERROR ACC EMPTY: ', inst)
                            pass
                    print('\n')
            else:
                print('NO ENTRIES FOR: ', domain)
            print('ACCOUNTS TOTAL: ', len(conn.response))
            conn.unbind()
            print('ACCOUNTS TO BE ADD: ', accounts_to_add)
            print('########## DOMAIN END ##########')

        except Exception as e:
            print("ERROR: ", domain, ' - ', e)
        # cleans NULL values from database
        finally:
            cursor.execute(delete)
            cnx.commit()
            cursor.close()
            cnx.close()
            ok = 'ADSYNC COMPLETE!'
    return ok
