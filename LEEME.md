# BAN DRUPAL SPAMMERS

Es un script escrito en python que sirve para ayudar a combatir el spam en
Drupal, tanto para reducir el numero de spammers como para reducir uno de sus
daños colaterales más dañinos, el consumo de ancho de banda.

Básicamente lo que hace es complementar a Mollom, uno de los módulos antispam
para Drupal, creado por el mismo creador de Drupal, Dries Buytaert. Este lee
las entradas del registro de Drupal que hace Mollom y toma nota de las IPs para
bloquearles el acceso a la página. Esto les remite a una simple página de texto
que reduce el consumo de ancho de banda y acaba frustrando antes los intentos
de insertar spam al carecer de ningún campo de formulario donde introducirlos.

La página a la que son redirigidos los atacantes es tan simple que ocupa entre
33 y 39 bytes. Es algo así:

    Sorry, 127.0.0.1 has been baned.

Donde 127.0.0.1 seria sustituido por la IP del atacante.

Para bloquear a estos spammers, emplea la opción que incorpora Drupal por
defecto para bloquear IPs en el sitio web, solo que en vez de emplear el
formulario incorporado las inserta directamente en la tabla access. Como el
llenar esta tabla de miles de registros acaba afectando al rendimiento de
Drupal (tiene que comparar la ip de cada visitante con las insertadas en la
tabla), existe un parámetro que regula el numero máximo de ips a permanecer en
la tabla. Cuando este número máximo es alcanzado, se rotan las IPs en la tabla
 eliminando las más antiguas. Para controlar cuando fueron introducidas las IPs
 se modifica la tabla access y se le añade un campo timestamp.


## FICHEROS

Fichero                  | Descripción
-------------------------|------------------------------------------------------
`ban_drupal_spammers.py` | fichero del script, el programa principal
`logger.py`              | modulo que permite crear un log elegante para enviar por correo o grabar en un fichero
`GeoIP.dat`              | fichero con los datos de geolocalización, para obtener el país de origen de las IPs de los spammers. Este fichero se obtiene de Maxmind, de su base de datos GeoIP
`map_by_country.py`      | pequeño script que sirve para crear un fichero xml con los datos para generar un mapa de amMap (http://www.ammap.com/), que enumera los spammers por países
`ammap_data.xml`         | fichero de ejemplo de salida de `map_by_country.py`

## REQUISITOS PREVIOS Y DEPENDENCIAS

### Para Linux (no testeado en Windows o Mac):

Lógicamente, lo primero que necesitamos para ejecutarlos es python. Si estamos
 en Linux normalmente viene instalado por defecto y no es un problema.

La versión de python necesaria para ejecutar el script es la 2.6

Este script emplea varios módulos que están presentes en la biblioteca estándar
de python, excepto dos:


**[MySQLdb](http://sourceforge.net/projects/mysql-python/)**

Este es el modulo que empleo para conectar con la base de datos MySQL de Drupal.

Instalarlo en Linux suele ser sencillo, ya que viene incluido en muchas
distribuciones, por ejemplo para instalarlo en Debian/Ubuntu:

    $ sudo apt-get install python-mysqldb


**[pygeoip](http://code.google.com/p/pygeoip/)**

Este modulo sirve para relacionar las IPs de los spammers con el país de origen
de la misma.

En Linux es necesario instalar antes el paquete setuptools, en Ubuntu/Debian:

    $ sudo apt-get install python-setuptools

luego, una vez instalado el paquete:

    $ sudo easy_install pygeoip


### Para Drupal:


Es necesario tener instalados y funcionando dos módulos.

**Database logging**

Es un modulo opcional del core, es decir que pertenece al núcleo y viene en la
instalación por defecto. Simplemente es necesario activarlo para que se puedan
registrar los eventos de Drupal, entre ellos los de Mollom. Es un modulo que
recomiendo tener siempre activado, pues es de gran utilidad para depurar los
errores que pueden darse en nuestro sitio.

Existe una opción, dentro de "registros y alertas" que nos permite determinar
la longitud máxima de este registro.


**Mollom**

Este modulo puede bajarse de <http://drupal.org/project/mollom> y es necesario
tenerlo instalado y activo para poder utilizar este script. Mollom es quizá el
mejor y menos intrusivo módulo antispam para Drupal.

Las instrucciones de instalación y configuración del modulo están en
<http://drupal.org/handbook/modules/mollom>



## INSTRUCCIONES


### ban_drupal_spammers.py

Es sencillo de utilizar, ya que no hay que hacer nada, solo ejecutarlo. Esta
pensado para que se ejecute automáticamente de forma programada, es decir, que
se ejecutara cada cierto tiempo.

Para ello emplearíamos cron en linux para establecer una programación periódica
del script.

Lo único que hay que hacer en el script es definir los parámetros necesarios
para ejecutarlo. Los parámetros hacen referencia a :

* la base de datos en la que se encuentran las tablas de nuestra instalación
  de Drupal
* la ruta donde está situado el necesario fichero GeoIP.dat
* los valores para poder emplear un servidor smtp externo (opcional) para
  enviar los correos con el resumen de la ejecución
* el parámetro que define el número de IPs máximas a bloquear.

Los parámetros a modificar se encuentran claramente identificados dentro del
script, englobados entre

    #===============================================================================
    # SCRIPT PARAMATERS
    #===============================================================================

y

    #===============================================================================
    # END PARAMETERS
    #===============================================================================

El script puede ejecutarse tanto desde una maquina remota como desde el propio
servidor donde se encuentra Drupal (siempre que soporte la ejecución de scripts
python). Para poder ejecutarlo de forma remota, debe poder accederse al servidor
 MySQL remotamente, no todos los hosting compartidos soportan esto.

La ejecución del script es extremadamente simple, simplemente haría falta
escribir algo similar en la línea de comandos:

    python ban_drupal_spammers.py


### logger.py & GeoIP.dat

No es necesario hacer nada con estos ficheros, únicamente han de estar presentes
 en la misma carpeta que `ban_drupal_spammers.py`


### map_by_country.py & ammap_data.xml

Estos archivos están presentes únicamente para mostrar el modo de generar el
mapa de amMap que se incluye en este 
[articulo](http://joedicastro.com/combatir_el_spam_en_drupal). Es un mapa de 
coropletas que  enumera la cantidad de ataques spam que recibe esa pagina por 
país de origen del ataque.



## REPOSITORIO

El código está alojado en un repositorio de Mercurial (hg) en BitBucket, así que
 puedes clonarlo directamente así:

    hg clone http://bitbucket.org/joedicastro/ban-drupal-spammers

También está alojado en un repositorio Git en GitHub, emplea este comando para
poder clonarlo:

    git clone git://github.com/joedicastro/ban-drupal-spammers.git



## CARACTERÍSTICAS

Cuando se ejecuta el script, se genera un log (`ban_drupal_spammers.log`) en el
mismo directorio del script, con los resultados de la ejecución, que se van
añadiendo al mismo en sucesivas ejecuciones. Al mismo tiempo, se envía un correo
 (al mailbox del usuario local que lo ejecuta ó a la cuenta configurada en el
script) con los mismos datos grabados en en log.

Un ejemplo de estos correos enviados es el siguiente:


    De: yourlocaluser@localhost
    Para:  example@example.com
    Asunto: Ban Drupal Spammers. Ins: 5 Del: 0 - Tuesday 10/12/10, 05:10:01


    SCRIPT =========================================================================
    ban_drupal_spammers (ver. 0.51)
    http://joedicastro.com

    Connected to your_database in localhost as your_database_user
    ================================================================================

    START TIME =====================================================================
                                                          Tuesday 10/12/10, 05:10:01
    ================================================================================

    SPAMMERS' IPS INSERTED _________________________________________________________

    5 IPs

    201.x.x.x   Mexico
    88.x.x.x    Turkey
    95.x.x.x    Kazakstan
    91.x.x.x    Russian Federation
    61.x.x.x    Thailand



    BANNED IPS _____________________________________________________________________

    Mollom: 1578 IPs
    Drupal: 4 IPs


    END TIME =======================================================================
                                                          Tuesday 10/12/10, 05:10:01
    ================================================================================



## CONTRIBUCIONES

Las contribuciones y las ideas son bienvenidas. Para contribuir a la mejora y 
evolución de este script, puedes enviar sugerencias o errores a través de el
sistema de issues.

## LICENCIA

Este script están sujeto a la [Licencia GPLv3 ](http://www.gnu.org/licenses/gpl.html)
