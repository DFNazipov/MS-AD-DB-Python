import datetime
import psycopg2
import uuid
import ldap3

AD_SERVER = "dc.innostage.test.ru"
AD_USER = "username@dc.innostage.test.ru"
AD_PASSWORD = "P@ssw0rd"
AD_BASE_DN = "dc=innostage, dc=test, dc=ru"

DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "P@ssw0rd"
DB_NAME = "database_ad"
DB_TABLE_1 = "users"
DB_TABLE_2 = "groups"
DB_TABLE_3 = "useringroup"

def get_data_ad():
    server = ldap3.Server(AD_SERVER)
    connection = ldap3.Connection(server, user=AD_USER, password=AD_PASSWORD)
    connection.bind()
    filter_search = "(&((objectClass=user))"
    attributes = ['objectGUID', 'userPrincipalName', 'sAMAccountName', 'givenName', 'sn', 'middleName', 'lastLogon', 'memberOf']
    connection.search = (AD_BASE_DN, filter_search, attributes)

    users = []
    groups = []
    for entry in connection.entries:
        if 'objectGUID' in entry:
            if 'sAMAccountName' in entry:
                user = {
                    'guid': str(uuid.UUID(bytes=entry.objectGUID.value)),
                    'upn': entry.userPrincipalName.value,
                    'username': entry.sAMAccountName.value,
                    'first_name': entry.givenName.value,
                    'last_name': entry.sn.value,
                    'middle_name': entry.middleName.value,
                    'last_logon': None if entry.lastLogon is None else datetime.fromtimestamp(
                        int(entry.lastLogon.value) / 10 ** 6),
                    'groups': [g.split(',')[0].split('=')[1] for g in entry.memberOf.values]
                }
                users.append(user)
            else:
                group = {
                    'guid': str(uuid.UUID(bytes=entry.objectGUID.value)),
                    'cn': entry.cn.value,
                    'name': entry.name.value
                }
                groups.append(group)

        connection.unbind()
        return users, groups


def insert_db(users, groups):
    conn = psycopg2.connect(dbname=DB_HOST, host=DB_HOST, user="DB_USER",
                            password=DB_PASSWORD, port="5433")
    cursor = conn.cursor()

    users_data = f"INSERT INTO {DB_TABLE_1} (guid, upn, username, first_name, last_name, middle_name, last_logon) " \
                 f"VALUES (%s, %s, %s, %s, %s, %s, %s) " \
                 f"ON CONFLICT (guid) DO UPDATE " \
                 f"SET upn=excluded.upn, username=excluded.username, first_name=excluded.first_name, " \
                 f"last_name=excluded.last_name, middle_name=excluded.middle_name, last_logon=excluded.last_logon"
    for user in users:
        values = (
            user['guid'],
            user['upn'],
            user['username'],
            user['first_name'],
            user['last_name'],
            user['middle_name'],
            user['last_logon']
        )
        cursor.execute(users_data, values)

        group_data = f"INSERT INTO {DB_TABLE_2} (guid, cn, group_name) VALUES " \
                     f"(%s, %s, %s) ON CONFLICT (guid) " \
                     f"DO UPDATE SET cn=excluded.cn, name=excluded.name"
    for group in groups:
        values = (
            group['guid'],
            group['cn'],
            group['name']
        )
        cursor.execute(group_data, values)

        useringroup_data = f"INSERT INTO {DB_TABLE_3} (guid, username, group_name) " \
                           f"VALUES (%s, %s, %s) ON CONFLICT (guid, group_name) DO NOTHING"
    for user in users:
        for group in user['groups']:
            cursor.execute(useringroup_data, (user['guid'], user['username'], group))

    conn.commit()
    conn.close()

ad_users, ad_groups = get_data_ad()
insert_db(ad_users, ad_groups)