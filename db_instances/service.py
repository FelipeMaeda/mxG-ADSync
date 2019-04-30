from django.shortcuts import get_object_or_404
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, SUBTREE
import mysql.connector
from decouple import config
from datetime import datetime
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
        FROM email_accounts 
        WHERE domain_id = %s 
        AND account = %s;
    '''

    search_account_alias = '''
        SELECT account_alias 
        FROM account_aliases 
        WHERE account_alias = %(account_alias)s 
        AND domain_alias = %(domain_alias)s 
        AND account = %(account)s 
        AND domain_id = %(domain_id)s;
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

    insert_new_account = '''
        INSERT INTO email_accounts(
            account, 
            domain_id, 
            created, 
            data_source, 
            updated, 
            group_name, 
            is_mail_list) 
        VALUES(
            %(account)s, 
            %(domain_id)s, 
            %(created)s, 
            %(data_source)s, 
            %(updated)s, 
            %(group_name)s, 
            %(is_mail_list)s);
    '''

    insert_new_account_alias = '''
        INSERT INTO account_aliases(
            account_alias, 
            domain_alias, 
            created, 
            data_source, 
            account, 
            domain_id) 
        VALUES(
            %(account_alias)s, 
            %(domain_alias)s, 
            %(created)s, 
            %(data_source)s, 
            %(account)s, 
            %(domain_id)s);
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
                acc_added = []
                acc_alias_added = []
                for entry in range(total_entries):
                    emails = conn.response[entry]['attributes']['mail']
                    print('EMAILS: ', emails)
                    print('ACCOUNT: ', emails[0])
                    print('ALIASES: ', emails[:])
                    account = emails[0].split("@")[0]
                    cursor.execute(search_account, (domain, account))
                    has_account = cursor.fetchone()
                    # add new account
                    if has_account is None:
                        acc_added.append(account)
                        now = datetime.now()
                        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                        new_account = {
                            'account': account,
                            'domain_id': domain,
                            'created': formatted_date,
                            'data_source': 'adladp',
                            'updated': formatted_date,
                            'group_name': None,
                            'is_mail_list': 0,
                        }
                        cursor.execute(insert_new_account, new_account)
                        # accept the change
                        cnx.commit()

                        new_account_alias = {
                            'account_alias': account,
                            'domain_alias': domain,
                            'created': formatted_date,
                            'data_source': 'adladp',
                            'account': account,
                            'domain_id': domain,
                        }
                        cursor.execute(insert_new_account_alias, new_account_alias)
                        # accept the change
                        cnx.commit()
                    # check if there are any aliases to add in specific account
                    if len(emails) > 1:
                        for email in emails[1:]:
                            print('EMAIL: ', email)
                            accountAlias = email.split("@")[0]
                            domainAlias = email.split("@")[1]
                            accounts_alias = {
                                'account_alias': accountAlias,
                                'domain_alias': domainAlias,
                                'account': account,
                                'domain_id': domain,
                            }
                            cursor.execute(search_account_alias, accounts_alias)
                            has_account_alias = cursor.fetchone()
                            if has_account_alias is None:
                                acc_alias_added.append(accountAlias)
                                now = datetime.now()
                                formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                                add_account_alias = {
                                    'account_alias': accountAlias,
                                    'domain_alias': domainAlias,
                                    'created': formatted_date,
                                    'data_source': 'adladp',
                                    'account': account,
                                    'domain_id': domain,
                                }
                                cursor.execute(insert_new_account_alias, add_account_alias)
                                # accept the change
                                cnx.commit()
                    try:
                        for ldap_attr in ldap_attrs:
                            print('LDAP ATT: ', ldap_attr)
                            cursor.execute(
                                properties_mx_name, (ldap_attr,))
                            mx_prop = cursor.fetchone()
                            ldap_prop = conn.response[entry]['attributes'][ldap_attr]
                            # check if a especifc ldap attribute value is empty
                            if len(ldap_prop) > 0:
                                print('CURR ATT: ', ldap_prop)
                                if isinstance(ldap_prop, list):
                                    data_l = {
                                        'account': account,
                                        'domain': domain,
                                        'name': mx_prop[0],
                                        'value': ldap_prop[0],
                                    }
                                    print('DATA: ', data_l)
                                    cursor.execute(
                                        create_or_update, data_l)
                                    # accept the change
                                    cnx.commit()
                                else:
                                    data_s = {
                                        'account': account,
                                        'domain': domain,
                                        'name': mx_prop[0],
                                        'value': ldap_prop,
                                    }
                                    print('DATA: ', data_s)
                                    cursor.execute(
                                        create_or_update, data_s)
                                    # accept the change
                                    cnx.commit()
                            else:
                                data_n = {
                                    'account': account,
                                    'domain': domain,
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
            print('ACCOUNTS INCLUDED: ', acc_added)
            print('ACCOUNTS ALIAS INCLUDED: ', acc_alias_added)
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
