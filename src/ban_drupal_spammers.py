#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
    ban drupal spammers.py: ban spammers in Drupal with Mollom's aid
"""

#==============================================================================
# This Script uses the Mollom reports in Drupal for ban spammers' ips and
# reduce the bandwith usage in the website.
#==============================================================================

#==============================================================================
#    Copyright 2010 joe di castro <joe@joedicastro.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#==============================================================================

__author__ = "joe di castro - joe@joedicastro.com"
__license__ = "GNU General Public License version 3"
__date__ = "15/05/2010"
__version__ = "0.52"

try:
    import sys
    import os
    import time
    import base64
    import collections
    import MySQLdb
    import pygeoip
    import logger
except ImportError:
    # Checks the installation of the necessary python modules
    print((os.linesep * 2).join(["An error found importing one module:",
    str(sys.exc_info()[1]), "You need to install it", "Exit..."]))
    sys.exit(-2)


def connect_db(host, user, pass_, db, port=3306):
    """Connect to MySQL database."""
    try:
        data_base = MySQLdb.connect(host=host, user=user, passwd=pass_, db=db,
                                    port=port, client_flag=65536)
        # flag 65536 is to allow multiple statements in a single string, equals
        # to CLIENT_MULTI_STATEMENTS
    except MySQLdb.OperationalError:
        print("Database connection fails, check that you gave the right "
              "credentials to access the database{0}Exit.".format(os.linesep))
        sys.exit(-2)
    return data_base


def select(curs, sql):
    """Runs a SQL SELECT query and returns a tuple as output."""
    curs.execute(sql)
    return curs.fetchall()


def alter_table(curs, db_table):
    """Create the aux field in the table if no exists, else do nothing."""
    database_string = """
                        ALTER TABLE {0}
                        ADD timestamp INT(11) NOT NULL DEFAULT '0';
                        """.format(db_table)
    try:
        curs.execute(database_string)
        return "Aux Field 'timestamp' in table '{0}' created.".format(db_table)
    except MySQLdb.OperationalError:
        print ("Can't create the aux field, seems this exists previously.")
        # This output is not reported in the log, it will be repetitive.


def ins_qstr(q_mask, q_timestamp):
    """Create a SQL INSERT query string for the given ip."""
    iqstr = """
            INSERT INTO `access`
            (mask, type, status, timestamp)
            VALUES ('{0}', 'host', '0', {1});{2}
            """.format(q_mask, q_timestamp, os.linesep)
    return iqstr


def del_qstr(q_timestamp):
    """Create a DELETE query string for the given timestamp."""
    dqstr = """
            DELETE FROM access
            WHERE timestamp='{0}';{1}
            """.format(q_timestamp, os.linesep)
    return dqstr


def ip_and_country(l_ips, geo):
    """Create the log lines about the ips and their countries."""
    output = None
    if l_ips:
        total = "{0} IPs".format(len(l_ips))
        ips_and_countries = [(geo.country_name_by_addr(l), l) for l in l_ips]
        ips = os.linesep.join(['{0:16} {1}'.format(i[1], i[0]) for  i in
                               sorted(ips_and_countries)])
        output = os.linesep.join([total, '', ips])
    return output


def renew_geoip(gip_path):
    """Check if the geoip data file is too old."""
    out_str = ''
    gz_file = ("http://geolite.maxmind.com/download/geoip/database/"
                "GeoLiteCountry/GeoIP.dat.gz")
    web_url = "http://www.maxmind.com/app/geolitecountry"
    geoip_file_date = os.path.getmtime(gip_path)
    if (time.time() - geoip_file_date) > 2592000:  # 2592000s = 30 days
        out_str += ("Your GeoIP data file* is older than 30 days!{0}{0}"
                    "You can look for a new version in:{0}{1}{0}or{0}{2}{0}{0}"
                    "  *{3}".format(os.linesep, gz_file, web_url, gip_path))
    return out_str


def main():
    """main section"""

#==============================================================================
# SCRIPT PARAMATERS
#==============================================================================

    # database host, name or ip ('localhost' by default)
    host = 'localhost'
    # database user name ('root' by default)
    user = 'root'
    # database password, with a minimum security measure, encoded by base64
    # ('password' by default)
    password = base64.b64decode('cGFzc3dvcmQ=')
    # database name ('database' by default)
    database = 'database'

    # path to geolocation data file GeoIP.dat
    geoip_path = '/your/path/to/file/GeoIP.dat'

    # mail server, smtp protocol, to send the log ('localhost' by default)
    smtp_server = 'localhost'
    # sender's email address ('' by default)
    from_addr = ''
    # a list of receiver(s)' email addresses ([''] by default)
    to_addrs = ['']
    # smtp server user ('' by default)
    smtp_user = ''
    # smtp server password, with a minimum security measure, encoded by base64
    # ('password' by default)
    smtp_pass = base64.b64decode('cGFzc3dvcmQ=')

    # set the perfomace threshold (number of banned ips) for you site
    threshold = 2000

#==============================================================================
# END PARAMETERS
#==============================================================================

    # Initialize the log
    log = logger.Logger()
    # log the header
    url = 'http://joedicastro.com'
    connected = 'Connected to {0} in {1} as {2}'.format(database, host, user)
    log.header(url, connected)

    # log the start time
    log.time('Start Time')

    # log the warning about old geolocation data file
    log.list('The GeoIp.dat file is old', renew_geoip(geoip_path))

    # connect to database, create the cursors & initialize the geolocation info
    mysql_db = connect_db(host, user, password, database)
    cursor = mysql_db.cursor()
    dict_cursor = mysql_db.cursor(MySQLdb.cursors.DictCursor)
    gip = pygeoip.GeoIP(geoip_path)

    # optimize the database (instead a cron task in the server)
    all_tables = [tabl[0] for tabl in select(cursor, "SHOW TABLES")]
    cursor.execute('OPTIMIZE TABLE {0}'.format(', '.join(all_tables)))

    # Adds the timestamp field to the 'access' table if no exists
    log.list('New aux table field created', alter_table(cursor, 'access'))

    # Query the database and obtain the result. We collect the 'access' table
    # ips and ips from spammers reported by Mollom in 'watchdog' table
    # access = ({'timestamp':timestamp, 'mask': 'ip'}, ...)
    # mollom = ({'timestamp':timestamp, 'mask': 'ip'}, ...)
    access = select(dict_cursor, """SELECT mask, timestamp FROM access""")

    mollom = select(dict_cursor, """SELECT hostname as mask, timestamp
                                    FROM `watchdog`
                                    WHERE `type` LIKE '%mollom%'
                                    AND `message` LIKE '%spam:%'""")

    # From the 'access' ips, select the ips blocked by this script from Mollom,
    # discarding those introduced through the Drupal administration interface
    # from_access = {'ip':timestamp, ...}
    from_access = {}
    for a_row in access:
        if int(a_row['timestamp']):
            from_access[a_row['mask']] = a_row['timestamp']

    # Here we select the ips that Mollom reported, if there are multiple
    # occurrences of the same ip, we always choose the most recent
    # from_mollom = {'ip':timestamp, ...}
    from_mollom = {}
    for m_row in mollom:
        if m_row['mask'] in from_mollom.keys():
            if int(from_mollom[m_row['mask']]) < int(m_row['timestamp']):
                from_mollom[m_row['mask']] = m_row['timestamp']
        else:
            from_mollom[m_row['mask']] = m_row['timestamp']

    # Now, from these ips, select the IPs of spammers that were not already
    # banned and generate queries to insert into the 'access' table. It's
    # necessary to check if some of ips reported through Mollom didn't be
    # already banned, because of how the Drupal's event log works. The optional
    # core module "Database logging" (which must be enabled to run his script)
    # is deleting records by the tail (into the 'watchdog' table) on each cron
    # run, according to a maximum limit set in the admin menu. This limit may
    # be 100, 1000, 10000, 100000, 1000000 records, as determined in the
    # "Loggin and alerts -> Database logging" menu. Then depending on the
    # record limit set in the 'watchdog' table, the frequency with which you
    # run the cron job and how often you run this script, it's  very likely
    # that in the previous query we have returned a number of ips that have not
    # yet eliminated from the log ('watchdog'), but we have already added to
    # the table of bannedd ips ('access'). This will avoid duplicate ips on
    # table 'access' ins_ips = ['ip0', 'ip1', ...]
    ins_ips = [f_ip for f_ip in from_mollom.keys() if f_ip not in from_access]
    query_str = ''.join(ins_qstr(i_ip, from_mollom[i_ip]) for i_ip in ins_ips)

    # number of banned ips through this script
    banned_ips = len(from_access) + len(ins_ips)
    # number of banned ips through Drupal administration interface
    drupal_banned_ips = len(access) - len(from_access)

    # After a certain number of records in the table 'access', the website's
    # perfomance deteriorates and from an even larger number, the behavior of
    # Drupal just become erratic. In the case of the site on which to run this
    # script, we see a clear loss of performance from the 3000 records and
    # becomes erratic over 5000. To avoid this unpleasant side effect, and
    # that cure don't be worse than the disease, I set a performance threshold
    # in 2000 records, from which records were removed from the table. If the
    # number of rows is greater than the performance threshold, we proceed to
    # calculate the ips to remove, selecting the oldest. The number of ips to
    # delete will be at least the 30% of "from_access". Just delete records
    # inserted through this script, never the inserted via Drupal admin
    # interface
    trigger = bool(len(access) > threshold)  # perfomance threshold

    del_ips, latest = [], 0  # ips to delete (if trigger) & latest ip's date

    if trigger:
        # Now we'll group the ips by date. Use the object
        # collections.defauldict to group the ips in a dictionary of lists
        # (values) of ips by date (keys)
        # ips_by_time = {timestamp:['ip0', ..], ...}
        ips_by_time = collections.defaultdict(list)
        for fa_ip in from_access:
            ips_by_time[from_access[fa_ip]].append(fa_ip)

        # We selected the oldest ips to have a number of them greater than or
        # equal to 30% of blocked by this script
        for ips_date in sorted(ips_by_time.keys()):
            if len(del_ips) < ((len(from_access) * 30) / 100):
                query_str += del_qstr(ips_date)  # delete by date, less queries
                for d_ip in ips_by_time[ips_date]:
                    del_ips.append(d_ip)
                    banned_ips -= 1
                if int(ips_date) > latest:
                    latest = int(ips_date)

        latest = time.strftime('%A %x', time.localtime(latest))

        # log spammers' ips deleted from the table
        log.list("Spammers' Ips deleted", ip_and_country(del_ips, gip))
        log.list("Newest date of deleted IPs", "Date: {0}".format(latest))

    # runs the database query
    if query_str:
        cursor.execute(query_str)

    # close database cursors
    cursor.close()
    dict_cursor.close()

    # log spammers' ips inserted into the table
    log.list("Spammers' IPs inserted", ip_and_country(ins_ips, gip))

    # log total banned ips by origin
    log.list('Banned IPs', ['Mollom: %d IPs' % banned_ips,
                            'Drupal: %d IPs' % drupal_banned_ips])
    # log the end time
    log.time('End Time')

    # send the log by email
    log.send('Ban Drupal Spammers. Ins: {0} Del: {1}'.
             format(len(ins_ips), len(del_ips)), send_from=from_addr,
             dest_to=to_addrs, mail_server=smtp_server, server_user=smtp_user,
             server_pass=smtp_pass)

    # write the log to a file
    log.write(True)

if __name__ == "__main__":
    main()
