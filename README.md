# BAN DRUPAL SPAMMERS

It is a script written in python which is used to help fight spam in Drupal, to
reduce the number of spammers and to reduce one of its most damaging collateral
damage, the large bandwidth consumption.

Basically what it does is to complement Mollom, an antispam module for Drupal,
created by the same creator of Drupal, Dries Buytaert. This reads the Drupal log
 entries from Mollom and records the IPs to block access to the site. And sends
them to a simple text page that reduces bandwith consumption and ends much
earlier to thwart their attempts to insert spam, because the page lacks any form
 field where they enter the spam.

The page that it's redirected to the attackers is so simple that it takes
between 33 and 39 bytes. It is something like:

    Sorry, 127.0.0.1 has been baned.

Where 127.0.0.1 will be replaced by the spammer IP

To block these spammers, using the option that incorporates Drupal by default to
 block IPs in the site, only instead of using the built form, they are inserted
directly into the table access. How to complete this table of thousands of
records ultimately affects the performance of Drupal (you have to compare the
IP of each visitor to the inserted in the table), there is a parameter that
governs the maximum number of ips to remain on the table. When this threshold is
 reached, rotate the IPs in the table by removing the oldest. To control when
the IPs were introduced, the table access is modified and added a field
timestamp.


## FILES

File                     | Description
-------------------------|-----------
`ban_drupal_spammers.py` | script file, the main program
`logger.py`              | module that allows you to create an elegant log to send by mail or write to a file
`GeoIP.dat`              | file with the geolocation data, for the country of origin of the IPs of spammers. This file is obtained from Maxmind of its database GeoIP
`map_by_country.py`      | small script used to create a file xml with the data to generate a map of amMap,  which lists the spammers by country
`ammap_data.xml`         | sample out file for `map_by_country.py`


## PRE-REQUISITES & DEPENDENCIES


### For Linux (no tested in Windows or Mac):

Obviously, first we need is python. If we are in Linux usually is installed by
default.

The python version needed for run both scripts is 2.6

This script uses several modules included in the python standard library, except
 two:


**[MySQLdb](http://sourceforge.net/projects/mysql-python/)**

This is the module I use to connect to the Drupal's MySQL database.

Linux install is usually straightforward, as it comes included in many
distributions, for example to install in Debian / Ubuntu:

    $ sudo apt-get install python-mysqldb


**[pygeoip](http://code.google.com/p/pygeoip/)**

This module serves to connect the IPs of the spammers with the country of origin

In Linux it is necessary to first install the setuptools package in
Ubuntu/Debian

    $ sudo apt-get install python-setuptools

Of course, once installed the package:

    $ sudo easy_install pygeoip



### For Drupal:


You need to have two modules installed and running.

**Database logging**


Is an optional module of the core and comes in the default installation. You
just have to activate it so you can record the events of Drupal, including those
 of Mollom. Is a module that I recommend to have always on, it is useful to
debug the errors that may occur on our site.

There is an option, under "Logs and Alerts" which allows us to determine the
maximum length of this record.

**Mollom**

This module can be downloaded from <http://drupal.org/project/mollom> and is
necessary to have it installed and running to use this script. Mollom is perhaps
 the best and least intrusive spam module for Drupal.

Install and configure instructions are in
<http://drupal.org/handbook/modules/mollom>


## INSTRUCTIONS


### ban_drupal_spammers.py

It is easy to use, because not to do anything, just run. It is meant to run
automatically on a schedule, ie to be executed periodically.

To do so would use cron on Linux to establish a regular schedule of the script.

All you have to do in the script is to define the parameters needed to run it.
The parameters refer to:

* The database in which tables are our Drupal installation
* The path where is located the necessary file GeoIP.dat
* Values in order to use an external SMTP server (optional) to send mails
  with the resume
* The parameter that defines the maximum number of IPs to block
  (stored in table).

The parameters to change are clearly identified within the script, enclosed
between

    #===========================================================================
    # SCRIPT PARAMATERS
    #===========================================================================

and

    #===========================================================================
    # END PARAMETERS
    #===========================================================================

The script can be run either from a remote machine and from the server itself
where Drupal (if supports the implementation of python scripts). To run it
remotely, must be accessible to remote MySQL server, not all shared hosting
support this.

Running the script is extremely simple, simply could write something similar on
the command line:

    python ban_drupal_spammers.py


### logger.py & GeoIP.dat

No need to do anything with these files only have to be present in the same
folder as `ban_drupal_spammers.py`


### map_by_country.py & ammap_data.xml

These files are used only to show how to generate a map of amMap included in
this [article](http://joedicastro.com/combatir_el_spam_en_drupal). Is a choropleth
 map that lists the number of spam attacks to receive this page by country of
origin of the attack.



## REPOSITORY

The code is hosted in a Git repository at GitHub, use this to get a clone:

    git clone git://github.com/joedicastro/ban-drupal-spammers.git


## FEATURES

When you run the script, it creates a log (`ban_drupal_spammers.log`) in the same
directory as the script, with the results of the execution, which are added to
it in successive executions. At the same time, an email is sent (to the local
user's mailbox that runs the script or to the account configured in the script)
with the same data recorded in log.

An example of these emails sent is:

    From:       yourlocaluser@localhost
    To:         example@example.com
    Subject:    Ban Drupal Spammers. Ins: 5 Del: 0 - Tuesday 10/12/10, 05:10:01


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

## CONTRIBUTION

Contributions and Feedback are most welcome.
To contribute to the improvement and development of this scripts, you can send
suggestions or bugs via the issues.


## LICENSE

The script is distributed under the terms of the
[GPLv3 license](http://www.gnu.org/licenses/gpl.html)

##### Apologies for any misspelling or syntax error, English isn't my mother tongue.
