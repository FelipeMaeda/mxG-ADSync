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

    delete_aliases = '''
        DELETE FROM account_aliases 
        WHERE domain_id = %s 
        AND account = %s;
    '''

    search_domain_aliases = '''
        select alias from domains_aliases 
        where domain = %s 
        and alias = %s;
    '''

    insert_new_domain_alias = '''
        INSERT INTO domains_aliases(
            alias, 
            created, 
            domain) 
        VALUES(
            %(alias)s, 
            %(created)s, 
            %(domain)s);
    '''

    insert_account_alias = '''
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

    accounts_updated = '''
        UPDATE email_accounts 
        SET updated = %(updated)s 
        WHERE domain_id = %(domain_id)s 
        AND account = %(account)s;
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
        # add date creation acc from ldap atts
        ldap_attrs.append('zimbraCreateTimestamp')
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
                # removes date creation acc from ldap atts to sync with mxgateway
                ldap_attrs.remove('zimbraCreateTimestamp')
                acc_added = []
                acc_alias_added = []
                domain_alias_add = []
                for entry in range(total_entries):
                    emails = conn.response[entry]['attributes']['mail']
                    account = emails[0].split("@")[0]
                    print('ACCOUNT: ', account)
                    print('ALIASES: ', emails[:])
                    cursor.execute(search_account, (domain, account))
                    has_account = cursor.fetchone()

                    # add new account
                    if has_account is None:
                        print('ADD ACC')
                        acc_added.append(account)
                        created_date = conn.response[entry]['attributes']['zimbraCreateTimestamp']
                        if isinstance(created_date, datetime):
                            print('CREATED AT: ', created_date)
                            formatted_created_at = created_date.strftime(
                                "%Y-%m-%d %H:%M:%S")
                        else:
                            now = datetime.now()
                            formatted_created_at = now.strftime(
                                '%Y-%m-%d %H:%M:%S')
                        now = datetime.now()
                        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                        new_account = {
                            'account': account,
                            'domain_id': domain,
                            'created': formatted_created_at,
                            'data_source': 'adladp',
                            'updated': formatted_date,
                            'group_name': None,
                            'is_mail_list': 0,
                        }
                        cursor.execute(insert_new_account, new_account)
                        # accept the change
                        cnx.commit()
                        print('ADD NEW ACCOUNT COMMITED')
                    try:
                        print("SYNCING LDAP ATT...")
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

                        print("UPDATING ALIASES...")
                        # cleans aliases in specific account
                        cursor.execute(delete_aliases, (domain, account))
                        # accept the change
                        cnx.commit()
                        # adds aliases
                        for email in emails:
                            now = datetime.now()
                            formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
                            accountAlias = email.split("@")[0]
                            domainAlias = email.split("@")[1]
                            # add domain alias if there is not created in mxgateway database yet
                            cursor.execute(search_domain_aliases,
                                        (domain, domainAlias))
                            has_domain_alias = cursor.fetchone()
                            if has_domain_alias is None:
                                domain_alias = {
                                    'alias': domainAlias,
                                    'created': formatted_date,
                                    'domain': domain,
                                }
                                cursor.execute(
                                    insert_new_domain_alias, domain_alias)
                                # accept the change
                                cnx.commit()
                                print('ADD DOMAIN ALIAS COMMITED')
                                domain_alias_add.append(domain_alias)
                            account_alias = {
                                'account_alias': accountAlias,
                                'domain_alias': domainAlias,
                                'created': formatted_date,
                                'data_source': 'adladp',
                                'account': account,
                                'domain_id': domain,
                            }
                            print('ACC ALIAS DATA: ', account_alias)
                            cursor.execute(insert_account_alias, account_alias)
                            # accept the change
                            cnx.commit()
                            print('ADD ACC ALIAS COMMITED')
                            acc_alias_added.append(accountAlias)
                            print('EMAIL: ', email)
                    except Exception as inst:
                        print('ERROR ACC EMPTY: ', inst)
                        pass

                    # sets updation date in all email accounts on synchronizations end
                    print('UPDATING...')
                    at = datetime.now()
                    updated_at = at.strftime('%Y-%m-%d %H:%M:%S')
                    updated_acc_sync = {
                        'updated': updated_at,
                        'domain_id': domain,
                        'account': account,
                    }
                    cursor.execute(accounts_updated, updated_acc_sync)
                    # accept the change
                    cnx.commit()
                    print('ACCs UPDATED AT: ', updated_at)
                    print('\n')
            else:
                print('NO ENTRIES FOR: ', domain)

            print('ACCOUNTS TOTAL: ', len(conn.response))
            conn.unbind()
            print('DOMIANS ALIAS INCLUDED: ', domain_alias_add)
            print('ACCOUNTS INCLUDED: ', acc_added)
            print('ACCOUNTS AND ALIAS UPDATED: ', acc_alias_added)
            print('########## DOMAIN END ##########')

        except Exception as e:
            cnx.rollback()
            print("ERROR: ", domain, ' - ', e)
        # cleans ldpa email accounts properties (NULL values) from database and closes conections
        finally:
            cursor.execute(delete)
            cnx.commit()
            cursor.close()
            cnx.close()
            ok = 'ADSYNC COMPLETE!'
    return ok
