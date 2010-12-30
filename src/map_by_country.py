#!/usr/bin/env python
# -*- coding: latin-1 -*-

"""
    map_by_country.py: make a ammap data file for a chropleth map of spammers.
"""

#===============================================================================
# This Script makes a ammap data file for create a chropleth map of spammers by
# country. At the end, uploads the file to a ftp server directory.
#
# ammap, http://www.ammap.com/
#
#===============================================================================

#===============================================================================
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
#===============================================================================

__author__ = "joe di castro <joe@joedicastro.com>"
__license__ = "GNU General Public License version 3"
__date__ = "30/12/2010"
__version__ = "0.4"

try:
    import sys
    import os
    import pygeoip
    import base64
    import time
    from ftplib import FTP
    from xml.dom.minidom import Document
    import MySQLdb
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
              "credentials to access the database{0}Exit...".format(os.linesep))
        sys.exit(-2)
    return data_base

def select(curs, sql):
    """Runs a SQL SELECT query and returns a tuple as output."""
    curs.execute(sql)
    return curs.fetchall()

def create_xml(spam_by_country, xml_file):
    """Create the ammap xml file with the spam_by_country data."""
    with open(xml_file, 'w') as ammap:
        doc = Document()
        os.environ['TZ'] = 'Europe/Madrid'
        fecha = time.strftime('%H:%M %d %B %Y')
        mapp = doc.createElement("map")
        mapp.setAttribute("map_file", "maps/world.swf")
        mapp.setAttribute("url", "#movie1")
        mapp.setAttribute("zoom", "100%")
        mapp.setAttribute("zoom_x", "0%")
        mapp.setAttribute("zoom_y", "0%")
        doc.appendChild(mapp)

        areas = doc.createElement("areas")
        mapp.appendChild(areas)

        for spammer in sorted(spam_by_country):
            area = doc.createElement("area")
            area.setAttribute("title", spammer)
            area.setAttribute("mc_name", spam_by_country[spammer][1])
            area.setAttribute("value", str(spam_by_country[spammer][0]))
            areas.appendChild(area)

        movies = doc.createElement("movies")
        mapp.appendChild(movies)

        movie = doc.createElement("movie")
        movie.setAttribute("file", "da.swf")
        movie.setAttribute("x", "5")
        movie.setAttribute("y", "364")
        movie.setAttribute("width", "150")
        movie.setAttribute("height", "32")
        movies.appendChild(movie)

        labels = doc.createElement("labels")
        mapp.appendChild(labels)

        label = doc.createElement("label")
        label.setAttribute("x", "0")
        label.setAttribute("y", "14")
        label.setAttribute("text_size", "18")
        label.setAttribute("width", "100%")
        label.setAttribute("align", "center")
        label.setAttribute("color", "#005000")
        text = doc.createElement("text")
        cdata = doc.createCDATASection("<b>Ataques de spam por pais</b>")
        text.appendChild(cdata)
        label.appendChild(text)
        labels.appendChild(label)

        label = doc.createElement("label")
        label.setAttribute("x", "0")
        label.setAttribute("y", "388")
        label.setAttribute("text_size", "8")
        label.setAttribute("width", "100%")
        label.setAttribute("align", "right")
        text = doc.createElement("text")
        cdata = doc.createCDATASection("Actualizado a {0}".format(fecha))
        text.appendChild(cdata)
        label.appendChild(text)
        labels.appendChild(label)

        ammap.write(doc.toprettyxml(indent="   ", encoding="UTF-8"))

def upload_ftp(host, ftp_user, ftp_pass, ftp_dir, to_upload, port=21):
    """Upload by FTP a file to a host."""
    with open(to_upload, 'r') as file_2_upload:
        ftp = FTP()
        ftp.connect(host, port)
        ftp.login(ftp_user, ftp_pass)
        ftp.cwd(ftp_dir)
        ftp.storbinary('STOR {0}'.format(os.path.basename(to_upload)),
                       file_2_upload)
        ftp.quit()


def main():
    """The main section"""

#===============================================================================
# SCRIPT PARAMETERS
#===============================================================================

    # the database host (localhost by default)
    host = 'localhost'
    # the database user (root by default) 
    user = 'root'
    # the database password with a minimum security step (by default, 'password'
    # in a base64 codec) 
    password = base64.b64decode('cGFzc3dvcmQ=')
    # the database name
    database = 'your_database_name'

    # Set if upload the file to a ftp server
    upload_to_ftp = False
    # the ftp user, secured in base64, for a minimum caution (default, 'user')
    ftp_user = base64.b64decode('dXNlcg==')
    # the ftp password (default in base64, 'ftp_password')
    ftp_pass = base64.b64decode('ZnRwX3Bhc3N3b3Jk')
    # the ftp directory
    ftp_dir = 'your/ftp/directory'

    # path to geoip data file
    ruta_geoip = '/your/path/to/file/GeoIP.dat'
    # path to store the ammap xml data file
    ammap_file_path = '/your/path/to/store/the/xml/data/file'

#===============================================================================
# END PARAMETERS
#===============================================================================

    # connect to database and create the cursor
    da_base = connect_db(host, user, password, database, 3306)
    cursor = da_base.cursor(MySQLdb.cursors.DictCursor)
    # get the data from db
    ips = select(cursor, """SELECT aid, mask
                            FROM access
                            WHERE timestamp > 1""")

    # initialize the geolocation info
    giop = pygeoip.GeoIP(ruta_geoip)
    # Get the geolocation info for ip
    # spammers = [(country, code, ip), ...]
    spammers = [(giop.country_name_by_addr(ip['mask']),
                 giop.country_code_by_addr(ip['mask']), ip['mask']) for
                  ip in ips]

    # Get the number of spammer by country in a dictionary
    # spammers_by_country = {country:[number of spammers, country code], ...}
    spammers_by_country = {}
    for spam_ip in spammers:
        if spam_ip[0]:
            if spam_ip[0] not in spammers_by_country.keys():
                spammers_by_country[spam_ip[0]] = [1, spam_ip[1]]
            else:
                spammers_by_country[spam_ip[0]][0] += 1

    # create the ammap xml data file
    ammap_file = os.path.join(ammap_file_path, 'ammap_data.xml')
    create_xml(spammers_by_country, ammap_file)
    # upload the ammap file to a ftp server
    if upload_to_ftp:
        upload_ftp(host, ftp_user, ftp_pass, ftp_dir, ammap_file)

if __name__ == "__main__":
    main()
