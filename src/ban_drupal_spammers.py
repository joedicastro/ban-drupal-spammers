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
#    Deberia haber recibido una copia de la Licencia Publica General GNU
#    junto a este programa.
#    En caso contrario, consulte <http://www.gnu.org/licenses/>.
#
#===============================================================================

__author__ = "joe di castro - joe@joedicastro.com"
__license__ = "GNU General Public License version 3"
__date__ = "15/05/2010"
__version__ = "0.2"

try:
    import sys
    import os
    import time
    import socket
    import base64
    import collections
    import _mysql
    import _mysql_exceptions
    import GeoIP
    import smtplib
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
        data_base = _mysql.connect(host, user, pass_, database, int(port),
                                   client_flag=65536)
        # El flag 65536 es para permitir multiples querys en una sola consulta
    except _mysql_exceptions.OperationalError:
        print  ("Database connection fails, check that you gave the right "
               "credentials to access the database\nQuitting...")
        sys.exit(-2)
    return data_base

def alter_table(database, db_table):
    """Create the aux field in the table if no exists, in other case, do nothing
    Crea el campo en la tabla si no existe, de otro modo, no hace nada"""
    output = ''
    database_string = """
                        ALTER TABLE {0}
                        ADD timestamp INT(11) NOT NULL DEFAULT '0';
                        """.format(db_table)
    try:
        database.query(database_string)
        output += 'Aux Field in table {0} created:\n'.format(db_table)
    except _mysql_exceptions.OperationalError:
        print ("Can't create the aux field, seems those exist previously.")
        # Esta salida no la reportamos en el log, pues será reiterativa.
    return output

def select_qry(database, sql):
    """Runs a SQL SELECT query and returns a dictionary as output
    Ejecuta una consulta SQL SELECT y devuelve el resultado como diccionario"""
    database.query(sql)
    result = database.store_result()
    qry_result = result.fetch_row(0, 1) # El "1" devuelve un dict y no una tupla
    return qry_result

def ins_qstr(q_mask, q_timestamp):
    """Create a SQL INSERT query string for the given ip
    Crea una cadena de consulta SQL INSERT para la ip dada"""
    iqstr = """
            INSERT INTO `access`
            (mask, type, status, timestamp)
            VALUES ('{0}', 'host', '0', {1});\n
            """.format(q_mask, q_timestamp)
    return iqstr

def del_qstr(q_timestamp):
    """Create a DELETE query string for the given timestamp
    Crean una cadena de consulta SQL DELETE para el timestamp dado"""
    dqstr = """
            DELETE FROM access
            WHERE timestamp='{0}';\n
            """.format(q_timestamp)
    return dqstr

def log_header(h_host, h_user, h_db):
    """Creates the header for the log
    Crea la cabecera del informe"""
    url = 'http://bitbucket.org/joedicastro/ban_drupal_spammers'
    header = '{0}\n{1:20} ver. {2}\n{3}\n\n'.format('=' * 70, __file__,
                                                    __version__, url)
    header += 'Connected to {0} in {1} as {2}'.format(h_db, h_host, h_user)
    return header

def log_time(t_string):
    """Creates de date/time lines for the log
    Crea las líneas de información de fecha/hora para el informe"""
    cur_time = '\n{0}\n{1:20}{2:>50}\n{0}\n\n'.format('=' * 70, t_string,
                                                    time.strftime('%A %x, %X'))
    return cur_time

def log_ips(l_msg, l_ips, geo):
    """Create the log lines about the ips situation
    Crea las lineas del informe para las distintas situaciones de las ips"""
    l_str = ''
    if l_ips:
        l_str += "{0} {1}\n\n".format(l_msg, len(l_ips))
        for lip in sorted([(geo.country_name_by_addr(i), i) for i in l_ips]):
            l_str += '{0:16} {1}\n'.format(lip[1], lip[0])
        l_str += '\n'
    return l_str

def renew_geoip(cr_dt, gip_path):
    """Check if the geoip data file is too old
    Comprueba si el fichero de geolocalizacion es demasiado antiguo"""
    out_str = ''
    geoip_file_date = os.path.getmtime(gip_path)
    if int(cr_dt) - geoip_file_date > 2592000: # 2592000s = 30 days
        out_str += "Your GeoIP data file* is older than 30 days!\n\n"
        out_str += "You can look for a new version in:\n\
http://geolite.maxmind.com/download/geoip/database/GeoLiteCountry/GeoIP.dat.gz\
\nor\nhttp://www.maxmind.com/app/ip-location\n\n  * {0}\n\n\n".format(gip_path)
    return out_str

def send_mail(content):
    """Send the mail with the log to the user's local mailbox
    Envia el correo con el informe al buzón del usuario local"""
    # Set the local mail address for the script' user
    email = '{0}@{1}'.format(os.getenv('LOGNAME'), socket.gethostname())
    subject = 'Remove IP Spammers - {0}'.format(time.strftime('%A %x, %X'))
    msg = ("From: {0}\nTo: {0}\nSubject: {1}\n{2}".
           format(email, subject, content))
    server = smtplib.SMTP('localhost')
    server.sendmail(email, email, msg)
    server.quit()
    return



def main():
    """main section - Seccion principal"""

#===============================================================================
# SCRIPT PARAMATERS
#===============================================================================

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

    # set the perfomace threshold (number of banned ips) for you site
    threshold = 2000

#===============================================================================
# END PARAMETERS
#===============================================================================

    # comenzamos creando las primeras lineas del informe y comprobamos la
    # antigüedad del fichero de datos de localizacion geografica por ip
    log = log_header(host, user, database)
    log += log_time('Start Time: ')
    log += renew_geoip(time.time(), geoip_path)

    # conectamos a la base de datos e inicializamos los datos de geolocalización
    bdd = connect_db(host, user, password, database, '3306')
    gip = GeoIP.open(geoip_path, GeoIP.GEOIP_CHARSET_UTF8)
    # añadimos el campo timestamp si no existe
    log += alter_table(bdd, 'access')

    # Consultamos la base de datos y obtenemos el resultado. Recogemos las ips
    # de la tabla access y las ips de los spammers reportados por Mollom en la
    # tabla watchdog
    access = select_qry(bdd, """SELECT mask, timestamp FROM access""")

    mollom = select_qry(bdd, """SELECT hostname as mask, timestamp
                                FROM `watchdog`
                                WHERE `type` LIKE '%mollom%'
                                AND `message` LIKE '%spam:%'""")

    # De las ips de access, seleccionamos las ips bloqueadas por este script a
    # partir de Mollom, descartando las que introducimos a traves de la interfaz
    # de administracion de Drupal
    from_access = {}
    for a_row in access:
        if int(a_row['timestamp']):
            from_access[a_row['mask']] = a_row['timestamp']

    # Aqui seleccionamos las ips que mollom nos reporta, si hay varias
    # ocurrencias de la misma ip elegimos siempre la más reciente.
    from_mollom = {}
    for m_row in mollom:
        if m_row['mask'] in from_mollom.keys():
            if int(from_mollom[m_row['mask']]) < int(m_row['timestamp']):
                from_mollom[m_row['mask']] = m_row['timestamp']
        else:
            from_mollom[m_row['mask']] = m_row['timestamp']

    # Ahora de estas ips, seleccionamos las Ips de spammers que no estaban ya
    # baneadas y generamos las consultas para insertarlas en la tabla. Es
    # necesario comprobar si las ips reportadas por Mollom no están ya
    # bloqueadas por como funciona el registro de eventos en Drupal. El modulo
    # del núcleo opcional Database logging (que debe estar activado para que
    # funcione este script) va eliminando registros por la cola (en la tabla
    # watchdog) en cada ejecución de cron en función de un limite máximo
    # establecido en el menú de administración. Este limite puede ser de 100,
    # 1000, 10000, 100000, 1000000 registros, según lo establezcamos en el menú
    # de registro de alertas. Luego dependiendo del limite de registros
    # establecido en esta tabla, la frecuencia con la que se ejecute la tarea
    # cron y la frecuencia con que se ejecute este script, es muy probable que
    # en la consulta anterior nos haya devuelto una serie de ips que aún no han
    # sido eliminadas del registro, pero que ya hayamos añadido a la tabla de
    # las ips bloqueadas. De este modo evitamos duplicar ips en la tabla de
    # ips bloqueadas
    ins_ips = [f_ip for f_ip in from_mollom.keys() if f_ip not in from_access]
    query_str = ''.join(ins_qstr(i_ip, from_mollom[i_ip]) for i_ip in ins_ips)

    # numero de ips baneadas a traves de este script
    banned_ips = len(from_access) + len(ins_ips)
    # numero de ips baneadas a traves del interface de Drupal
    drupal_banned_ips = len(access) - len(from_access)

    # A partir de cierto numero de registros en la tabla access, el rendimiento
    # de la pagina se deteriora y a partir de un numero aun mayor, el
    # comportamiento de Drupal se acaba volviendo erratico. En el caso del sitio
    # sobre el que se va a ejecutar este script, se aprecia una perdida de
    # rendimiento a partir de los 3000 registros y se vuelve erratico sobre los
    # 5000. Para prevenir este desagradable efecto secundario, y que no sea peor
    # el remedio que la enfermedad, establezco un umbral de rendimiento en los
    # 2500 registros, a partir del cual ire eliminando registros de la tabla.
    # Si el numero de registros es mayor al umbral de rendimiento, procedemos
    # a calcular las ips a eliminar, seleccionando las más antiguas. El numero
    # de las ips a borrar sera un minimo del 30% de from_access. Solo
    # eliminaremos registros introducidos a traves de este script, nunca los
    # introducimos a traves del interface de Drupal

    trigger = bool(len(access) > threshold) # Umbral de rendimiento

    if trigger:
        # Ahora vamos a  agrupar las ips por fechas. Utilizo el objeto
        # defaultdict del modulo collections para agrupar las ips en un
        # diccionario de listas(values) de ips por fecha(keys)
        ips_by_time = collections.defaultdict(list)
        for fa_ip in from_access:
            ips_by_time[from_access[fa_ip]].append(fa_ip)

        del_ips, newest = [], 0    # ips a borrar y fecha de la ip mas reciente

        # Seleccionamos las ips mas antiguas hasta tener un numero de ellas
        # mayor o igual al 30% de las bloqueadas por este script
        for ips_date in sorted(ips_by_time.keys()):
            if len(del_ips) < ((len(from_access) * 30) / 100):
                query_str += del_qstr(ips_date) # borramos por fecha, - querys
                for d_ip in ips_by_time[ips_date]:
                    del_ips.append(d_ip)
                    banned_ips -= 1
                if int(ips_date) > newest:
                    newest = int(ips_date)

        newest = time.strftime('%A %x', time.localtime(newest))
        log += log_ips("Spammers' Ips deleted:", del_ips, gip)
        log += "Newest date of Ips deleted: {0}\n".format(newest)

    # lanzamos la consulta a la base de datos
    if query_str:
        bdd.query(query_str)

    # Recogemos los ultimos datos para el informe
    log += log_ips("Spammers' Ips inserted:", ins_ips, gip)
    log += '\nTotal Banned Ips through Mollom: {0}\n'.format(banned_ips)
    log += '\nBanned through Drupal: {0}\n'.format(drupal_banned_ips)
    log += log_time('End Time: ')

    # enviamos el informe por mail
    send_mail(log)

if __name__ == "__main__":
    main()

