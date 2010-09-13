#!/usr/bin/env python
# -*- coding: utf8 -*-

"""
    logger.py: Create a log object to log script messages
"""

#===============================================================================
# This module does...
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

__author__ = "joe di castro - joe@joedicastro.com"
__license__ = "GNU General Public License version 3"
__date__ = "10/09/2010"
__version__ = "0.10"

try:
    import sys
    import os
    import time
    import smtplib
    import socket
except ImportError:
    # Checks the installation of the necessary python modules 
    print((os.linesep * 2).join(["An error found importing one module:",
    str(sys.exc_info()[1]), "You need to install it", "Stopping..."]))
    sys.exit(-2)

class Logger():
    """Create a log object to log script messages."""

    def __init__(self):
        self.__log = ''
        self.__script_name = os.path.basename(__file__).split('.')[0]

    def __len__(self):
        return len(self.__log)

    def __format__(self, tit, cont, decor):
        """Format a block or a list of lines to enhance comprehension.
        
        (str) tit -- title for the block or list
        (str or iterable) cont -- line/s for the list/block content
        ('=' or '_') decor - define if it's list or block and decorate it
        
        make the looks of self.block() and self.list() 
        
        """
        ending = {'=':'', '_':os.linesep}[decor]
        end = {'=': '=' * 80, '_':''}[decor]
        begin = ' '.join([tit.upper(), (80 - (len(tit) + 1)) * decor]) + ending
        cont = [cont] if isinstance(cont, str) else cont
        sep = os.linesep
        self.__log += sep.join([begin, sep.join(cont), end, sep])

    def block(self, title, content):
        """A block of text lines headed and followed by a line full of '='.
        
        (str) title -- The title that start the first line of '='
        (str or iterable) content -- The line/s between the '=' lines
        
        There's not any empty line between the '=' lines and content, e.g.:
        
        TITLE ==================================================
        content
        ========================================================
        
        """
        if content:
            self.__format__(title, content, '=')

    def list(self, title, content):
        """A list of text lines headed by a line full of '_'.
               
        (str) title -- The title that start the line of '_'
        (str or iterable) content -- The line/s after the '_' line
        
        After the '_' line is a empty line between it and the content, e.g.:
        
        TITLE __________________________________________________
        
        content
        
        """
        if content:
            self.__format__(title, content, '_')

    def free(self, content):
        """Free text unformatted.
        
        (str) content -- Text free formated
        
        """
        if isinstance(content, str):
            self.__log += content + os.linesep * 2

    def time(self, title):
        """A self.block() formated line with current time and date.
        
        (str) title -- Title for self.block()
        
        Looks like this, the data and time are right-justified:
        
        TITLE ==================================================
                                       Friday 09/10/10, 20:01:39
        ========================================================
        
        """
        self.block(title, '{0:>80}'.format(time.strftime('%A %x, %X')))

    def header(self, url, msg):
        """A self.block() formated header for the log info.
        
        (str) url -- The url of the script
        (str) msg -- Message to show into the header. To Provide any useful info
        
        It looks like this:
        
        SCRIPT =================================================
        script name and version
        url
        
        msg
        ========================================================
        
        """
        script = '{0} (ver. {1})'.format(self.__script_name, __version__)
        self.block('Script', [script, url, '', msg])

    def get(self):
        """Get the log content."""
        return self.__log

    def send(self, subject):
        """Send a mail with the log to the user's local mailbox.
        
        (str) subject - A string for the mail's subject. 
        
        Date and time info is added to the end of the subject  
        
        """
        # Set the local mail address for the script' user
        email = '{0}@{1}'.format(os.getenv('LOGNAME'), socket.gethostname())
        subject = '{0} - {1}'.format(subject, time.strftime('%A %x, %X'))
        msg = ("From: {0}{3}To: {0}{3}Subject: {1}{3}{2}".
               format(email, subject, self.__log, os.linesep))
        server = smtplib.SMTP('localhost')
        server.sendmail(email, email, msg)
        server.quit()
        return

    def write(self, append=False):
        """Write the log to a file.
        
        The name of the file will be like this: 
        
        script.log
        
        where 'script' is the name of the script file without extension (.py)
        
        (boolean) append -- If true appends log to file, else writes a new one 
        
        """
        mode = 'ab' if append else 'wb'
        with open('{0}.log'.format(self.__script_name), mode) as log_file:
            log_file.write(self.__log)

def main():
    """Main section"""
    url = 'http://bitbucket.org/joedicastro'
    head = 'This is a test of class Logger'

    log = Logger()
    log.header(url, head)
    log.time('Start time')
    log.block('Block', 'This is a sample of Logger.block()'.split(' '))
    log.list('List', 'This is a sample of Logger.list()'.split(' '))
    log.free('''Tis a sample of free text.
"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Pellentesque sed 
tortor eget justo vehicula consequat vel eu quam. Suspendisse non lectus eget 
orci varius adipiscing."''')
    log.time('End time')
    log.send('This is mail test')
    log.write(True)
    print(log.get())


if __name__ == "__main__":
    main()
