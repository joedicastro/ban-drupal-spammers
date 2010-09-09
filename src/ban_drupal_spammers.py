#!/usr/bin/env python
# -*- coding: latin-1 -*-

"""
    ban drupal spammers.py: ban spammers in Drupal with Mollom's aid
"""

#===============================================================================
# This Script uses the Mollom reports in Drupal for ban spammers' ips and 
# reduce the bandwith usage in the website.
#
# Este script emplea los informes de Mollom en Drupal para bloquear las ips de 
# los spammers y asi reducir el trafico (ancho de banda usado) en el sitio.
#===============================================================================

#===============================================================================
#    Copyright 2009 joe di castro <joe@joedicastro.com>
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
#
#    Este programa es software libre: usted puede redistribuirlo y/o modificarlo
#    bajo los términos de la Licencia Publica General GNU publicada 
#    por la Fundación para el Software Libre, ya sea la versión 3 
#    de la Licencia, o (a su elección) cualquier versión posterior.
#
#    Este programa se distribuye con la esperanza de que sea útil, pero 
#    SIN GARANTIA ALGUNA; ni siquiera la garantía implícita 
#    MERCANTIL o de APTITUD PARA UN PROPOSITO DETERMINADO. 
#    Consulte los detalles de la Licencia Publica General GNU para obtener 
#    una información mas detallada. 
#
#    Deberla haber recibido una copia de la Licencia Publica General GNU 
#    junto a este programa. 
#    En caso contrario, consulte <http://www.gnu.org/licenses/>.
#
#===============================================================================

__author__ = "joe di castro - joe@joedicastro.com"
__license__ = "GNU General Public License version 3"
__date__ = "21/10/2009"
__version__ = "0.10"

try:
    import sys
    import os
    import time
    import socket
    import base64
    import _mysql
    import _mysql_exceptions
    import GeoIP
    from smtplib import SMTP
except ImportError:
    # Checks the installation of the necessary python modules 
    # Comprueba si todos los módulos necesarios están instalados
    print((os.linesep * 2).join(["An error found importing one module:",
    str(sys.exc_info()[1]), "You need to install it", "Stopping..."]))
    sys.exit(-2)

def connect_db(host, user, pass_, database, port):
    """Connect to MySQL database.
    Conecta con la base de datos MySQL"""
    try:
        data_base = _mysql.connect(host, user, pass_, database, int(port))
    except _mysql_exceptions.OperationalError:
        print  ("Database connection fails, check that you gave the right "
               "credentials to access the database\nQuitting...")
        sys.exit(-2)
    return data_base

def query_db(database, sql):
    """Runs a SELECT query and shows the output 
    Ejecuta una consulta SELECT contra la BDD y devuelve el output"""
    database.query(sql)
    result = database.store_result()
    output = result.fetch_row(0)
    return output

def print_header(host, user, database):
    """Creates the header for the log
    Crea la cabecera del informe """
    url = 'http://bitbucket.org/joedicastro/ban_drupal_spammers'
    header = '{0}\n{1:20} ver. {2}\n{3}\n\n'.format('=' * 70, __file__,
                                                    __version__, url)
    header += 'Connected to {0} in {1} as {2}'.format(database, host, user)
    return header

def current_time(string):
    """Creates de date/time lines for the log 
    Crea las líneas de información de fecha/hora para el informe"""
    cur_time = '\n{0}\n{1:20}{2:>50}\n{0}\n\n'.format('=' * 70, string,
                                                    time.strftime('%A %x, %X'))
    return cur_time

def send_mail(content):
    """Send the mail with the log to the user's local mailbox
    Envia el correo con el informe al buzón del usuario local"""
    # Set the local mail address for the script' user
    email = '{0}@{1}'.format(os.getenv('LOGNAME'), socket.gethostname())
    subject = 'Remove IP Spammers - {0}'.format(time.strftime('%A %x, %X'))
    msg = ("From: {0}\nTo: {0}\nSubject: {1}\n{2}".
           format(email, subject, content))
    server = SMTP('localhost')
    server.sendmail(email, email, msg)
    server.quit()
    return

def main():
    """main section - Seccion principal"""

#===============================================================================
# SCRIPT PARAMETERS
#===============================================================================

    # the database host ('localhost' by default)
    host = 'localhost'
    # the database user ('root' by default)
    user = 'root'
    # the database password, with a minimum security step, encoded with base64 
    # ('user' by default)
    password = base64.b64decode('dXNlcg==')
    # the database name ('database' by default)
    database = 'database'

    # tha path of geolocation data file GeoIP.dat
    ruta_geoip = '/your/path/to/the/file/GeoIP.dat'

#===============================================================================
# END PARAMETERS
#=============================================================================== 

    # Primero obtenemos los datos que nos van a dar la localización geográfica 
    # de cada Ip. Para ello empleamos el fichero GeoIP.dat que bajaremos de 
    # http://www.maxmind.com/app/geolitecountry para tener la versión más
    # actualizada posible
    gip = GeoIP.open(ruta_geoip, GeoIP.GEOIP_CHARSET_UTF8)

    # creamos la cabecera del informe y anotamos la hora de comienzo
    log = ''
    log += print_header(host, user, database)
    log += current_time('Start Time: ')

    # Nos conectamos a la base de datos
    bdd = connect_db(host, user, password, database, '3306')
    # Consultamos las Ips bloquedas actualmente en Drupal
    banned_ip = query_db(bdd, """SELECT mask FROM access WHERE status=0""")
    # Consultamos las Ips unicas que Mollom ha detectado como comment spammers
    spammers = query_db(bdd, """SELECT DISTINCT hostname 
                            FROM `watchdog` 
                            WHERE `type` LIKE '%mollom%' 
                            AND `message` LIKE '%spam:%'""")
    new_spam_ips = []
    string4query = ''
    # Ahora buscamos de las Ips que nos ha reportado Mollom, las que no están 
    # ya bloqueadas y preparamos una cadena para realizar una sola query a la 
    # base de datos. Es necesario comprobar si las ips reportadas por Mollom no
    # están ya bloqueadas por como funciona el registro de eventos en Drupal.
    # El modulo del núcleo opcional Database logging (que debe estar activado 
    # para que funcione este script) va eliminando registros por la cola (en la
    # tabla watchdog) en cada ejecución de cron en función de un limite máximo 
    # establecido en el menú de administración. Este limite puede ser de 100, 
    # 1000, 10000, 100000, 1000000 registros, según lo establezcamos en el menú
    # de registro de alertas. Luego dependiendo del limite de registros 
    # establecido en esta tabla, la frecuencia con la que se ejecute la tarea 
    # cron y la frecuencia con que se ejecute este script, es muy probable que 
    # en la consulta anterior nos haya devuelto una serie de ips que aún no han 
    # sido eliminadas del registro, pero que ya hayamos añadido a la tabla de 
    # las ips bloqueadas. De este modo evitamos duplicar ips en la tabla de ips 
    # bloqueadas
    for spam_ip in spammers:
        if spam_ip not in banned_ip:
            string4query += "('{0}', 'host', '0'), ".format(spam_ip[0])
            new_spam_ips.append(spam_ip[0])

    # Ahora, si tenemos nuevas Ips de spammers para bloquear, ejecutamos la
    # query contra la base de datos con todas las nuevas Ips que serán añadidas.
    # Además generamos la lista de ips para el informe, con su localización
    # geográfica.
    if string4query:
        bdd.query("""INSERT INTO `access` 
                    (mask, type, status) 
                    VALUES {0}""".format(string4query[:-2]))
        log += 'Ips spammers insertadas: {0}\n\n'.format(len(new_spam_ips))
        new_spam_ips.sort()
        for new_ip in new_spam_ips:
            log += '{0:16} {1}\n'.format(new_ip,
                                        gip.country_name_by_addr(new_ip))

    # Cerramos el informe con un resumen del estado de las ips bloquedas y
    # añadimos la hora de finalización del script.
    log += '\nIps bloqueadas: {0}\n'.format(len(banned_ip) + len(new_spam_ips))
    log += current_time('End Time: ')
    # Por útimo mandamos el mail con el informe al usuario del sistema.
    send_mail(log)

if __name__ == "__main__":
    main()

