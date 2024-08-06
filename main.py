import psycopg2
import ldap3

AD_IP = "192.168.163.158"
AD_USER = "Администратор@innostage.local"
AD_PASSWORD = "P@ssw0rd"
AD_BASE_DN = "dc=innostage,dc=local"


DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "P@ssw0rd"
DB_NAME = "database_ad"
DB_TABLE_1 = "users_ad"
DB_TABLE_2 = "groups_ad"
DB_TABLE_3 = "usersingroups_ad"

def get_users_data_ad(ip,search_base,win_bind_name,win_bind_passwd):
    server = ldap3.Server('ldap://{}'.format(ip))
    search_filter_user = "(&(objectClass=person)(sAMAccountName=*))"
    attrs_user = ['objectGUID', 'userPrincipalName', 'sAMAccountName', 'givenName', 'sn', 'middleName', 'lastLogon', 'memberOf']
    with ldap3.Connection(server,user=win_bind_name,password=win_bind_passwd) as conn:
        conn.search(search_base, search_filter_user, attributes=attrs_user)
        users = []
        for entry in conn.entries:
            user = {
                'guid_user': str(entry.objectGUID),
                'upn': entry.userPrincipalName.value,
                'username': entry.sAMAccountName.value,
                'first_name': entry.givenName.value,
                'last_name': entry.sn.value,
                'middle_name': entry.middleName.value,
                'last_logon': str(entry.lastLogon),
                'member_of': tuple(entry.memberOf)
            }
            users.append(user)
        return users



def get_groups_data_ad(ip,search_base,win_bind_name,win_bind_passwd):
    server = ldap3.Server('ldap://{}'.format(ip))
    search_filter_group = "(&(objectClass=group)(sAMAccountName=*)(cn=*))"
    attrs_group = ['objectGUID','cn','name', 'distinguishedName']
    with ldap3.Connection(server,user=win_bind_name,password=win_bind_passwd) as conn:
        conn.search(search_base, search_filter_group, attributes=attrs_group)
        groups = []
        for entry in conn.entries:
            group = {
                'guid_group': str(entry.objectGUID),
                'cn': entry.cn.value,
                'group_name': entry.name.value,
                'distinguished_name': str(entry.distinguishedName)
            }
            groups.append(group)
        return groups

def insert_db(users, groups, DB_NAME, DB_HOST, DB_USER, DB_PASSWORD):
    conn = psycopg2.connect(dbname=DB_NAME, host=DB_HOST, user=DB_USER,
                            password=DB_PASSWORD, port="5433")
    cursor = conn.cursor()

    users_data = f"INSERT INTO {DB_TABLE_1} (guid_user, upn, username, first_name, last_name, middle_name, last_logon) " \
                 f"VALUES (%s, %s, %s, %s, %s, %s, %s) " \
                 f"ON CONFLICT (guid_user) DO UPDATE " \
                 f"SET upn=excluded.upn, username=excluded.username, first_name=excluded.first_name, " \
                 f"last_name=excluded.last_name, middle_name=excluded.middle_name, last_logon=excluded.last_logon"
    for user in users:
        values = (
            user['guid_user'],
            user['upn'],
            user['username'],
            user['first_name'],
            user['last_name'],
            user['middle_name'],
            user['last_logon']
        )
        cursor.execute(users_data, values)

        group_data = f"INSERT INTO {DB_TABLE_2} (guid_group, cn, group_name) VALUES " \
                     f"(%s, %s, %s) ON CONFLICT (guid_group) " \
                     f"DO UPDATE SET cn=excluded.cn, group_name=excluded.group_name"
    for group in groups:
        values = (
            group['guid_group'],
            group['cn'],
            group['group_name']
        )
        cursor.execute(group_data, values)

    usersingroups_data = f"INSERT INTO {DB_TABLE_3} (user_guid, group_guid, user_name, group_name) " \
                           f"VALUES (%s, %s, %s, %s) ON CONFLICT (user_guid, group_guid) DO UPDATE" \
                         f" SET user_name=excluded.user_name, group_name=excluded.group_name"
    for user in users:
        gr_us = tuple(user['member_of'])
        for grN in gr_us:
            for group in groups:
                if grN == group['distinguished_name']:
                    cursor.execute(usersingroups_data, (user['guid_user'], group['guid_group'], user['username'],
                                   group['group_name']))
                else:
                    continue

    conn.commit()
    conn.close()


ad_users = get_users_data_ad(AD_IP, AD_BASE_DN, AD_USER, AD_PASSWORD)
ad_groups = get_groups_data_ad(AD_IP, AD_BASE_DN, AD_USER, AD_PASSWORD)
insert_db(ad_users, ad_groups, DB_NAME, DB_HOST, DB_USER, DB_PASSWORD)
