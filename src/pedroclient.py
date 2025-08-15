
#  Copyright (C) 2006, 2007, 2008 Peter Robinson
#  Email: pjr@itee.uq.edu.au
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

""" Pedro client module.

This module defines the client interface for Pedro.

This is a simplified version of pedroclient.py from the
Pedro release and is aimed specifically at the Raspberry Pi
Pico running micropython.
"""

import re, socket, _thread, select
import sys

# For encoding and decoding messages sent over the socket.
def to_str(b):
    return b.decode("utf-8")
def from_str(b):
    return b.encode('utf-8')
    

running = True

class Reader:
    """The message reader thread. This runs a thread that
    reads incoming Pedro messages and processes them
    using the user defined callback function."""

    def __init__( self, sock, callback):
        self.sock = sock
        self.callback = callback
        _thread.start_new_thread(self.run, ())

    def run( self):
        buff = ""
        while (running):
            chars = self.sock.recv(1024)
            if (chars == ''):
                break
            buff = buff + to_str(chars)
            pos = buff.find('\n')
            while (pos != -1):
                message = buff[:pos]
                # ignore the rock
                _, message = message.split(" ", 1)
                self.callback(message)
                buff = buff[(pos+1):]
                pos = buff.find('\n')

# for testing if a P2P address is a variable
_p2p_var_addr = re.compile("^[_A-Z][^:]*$")

class PedroClient:
    """ A Pedro Client.

    The client is connected to the server on initialization.
    The methods are:
    disconnect() - disconnect from server
    
    connect() - reconnect to server
    
    notify(term) - send a notification to the server - term is
    a string representation of a Prolog term - 1 is returned if
    the server accepts term; 0 otherwise.

    subscribe(term, goal) - subscribe to terms that match term and
    that satisfy goal. Both term and goal are string representations
    of Prolog terms. The ID of the subscription is returned. The ID is
    0 if the subscription failed.

    unsubscribe(id) - unsubscribe to a previous subscription with ID id
    - ID is returned if the server succeeds in unsubscribing; otherwise
    0 is returned.

    register(myname) - register myname as my name with the server - 0 is
    returned iff registration failed.

    deregister() - deregister with server.

    p2p(addr, term) - send term as a p2p message to addr.

    get_notification() - get the first notification from the message queue
    of notifications sent from the server as a string.

    get_term() - the same as get_notification except the message is parsed
    into a representation of a Prolog term - see PedroParser.

    notification_ready() - test if a notification is ready to read.

    parse_string(string) - parse string into a Prolog term.
    """
    
    def __init__(self, ip_addr, callback, machine='localhost',
                 port=4550):
        """ Initialize the client.
        ip_addr -- the IP address of this client
                      - used for peer-to-peer messages.
        callback -- a user defined function used to process each
                    received message (the argument to the callback)
        machine -- then address of the machine the Pedro server is running.
        port -- the port the Pedro server is using for connections.  
        """
        self.machine = machine
        self.port = port
        self.connected = False
        self.callback = callback
        self.connect()
        self.name = ''
        self.my_machine_name = ip_addr
        self.reader = None
        
    def getDataSocket(self):
        """ Get the Data Socket """

        return self.datasock

    def connect(self):
        """ Make the connection to Pedro. """
        
        if (self.connected):
            return 0
        else:
            running = True
            # connect to info
            infosock = socket.socket()
            infosock.connect((self.machine, self.port))
            # get info from server on info socket
            pos = -1
            buff = ''
            while (pos == -1):
                chars = infosock.recv(64)
                buff = buff + to_str(chars)
                pos = buff.find('\n')
            parts = buff.split()
            self.machine = parts[0]
            ack_port = int(parts[1])
            data_port = int(parts[2])
            infosock.close()
            # connect to ack
            self.acksock = socket.socket()
            self.acksock.connect((self.machine, ack_port))
            # get my ID
            pos = -1
            buff = ''
            while (pos == -1):
                chars = self.acksock.recv(32)
                buff = buff + to_str(chars)
                pos = buff.find('\n')
            self.id_string = buff
            # connect to data
            self.datasock = socket.socket()
            self.datasock.connect((self.machine, data_port))
            self.datasock.send(from_str(self.id_string))
            # get ok from server on data socket
            pos = -1
            buff = ''
            while (pos == -1):
                chars = self.datasock.recv(32)
                buff = buff + to_str(chars)
                pos = buff.find('\n')
            if buff != 'ok\n':
                try:
                    self.acksock.shutdown(socket.SHUT_RDWR)
                    self.acksock.close()
                    self.datasock.shutdown(socket.SHUT_RDWR)
                    self.datasock.close()
                except:
                    pass
                return 0
            
            
            #self.parser = PedroParser()
            self.connected = True
            

    def disconnect(self):
        """ Disconnect the client. """
        
        if (self.connected):
            running = False
            self.connected = False
            try:
                self.acksock.shutdown(socket.SHUT_RDWR)
                self.acksock.close()
                self.datasock.shutdown(socket.SHUT_RDWR)
                self.datasock.close()
            except:
                pass
            return 1
        else:
            return 0
                    
    def get_ack(self):
        """ Get an acknowledgement from the server. """
        
        pos = -1
        buff = ''
        while (pos == -1):
            chars = self.acksock.recv(32)
            buff = buff + to_str(chars)
            pos = buff.find('\n')
        r = int(buff)   
        return r
    
    def notify(self, term):
        """ Send a notification to the server and return the ack. """
        
        if (self.connected):
            self.datasock.send(from_str(str(term)+'\n'))
            return self.get_ack()
        else:
            return 0
            
    def subscribe(self, term, goal = "true", rock = 0):
        """ Send a subscription to the server and return the ack. """
        # If a subscription is made then the reader needs
        # to be created if it doesn't already exist.
        if (self.reader is None):
            self.reader = Reader(self.datasock, self.callback)

        if (self.connected):
            self.datasock.send(from_str('subscribe(' + str(term) + ', (' +
                           str(goal) + '), ' + str(rock) + ')\n'))
            return self.get_ack()
        else:
            return 0


    def unsubscribe(self, id):
        """ Send an unsubscription to the server and return the ack. """
        
        if (self.connected):
            self.datasock.send(from_str('unsubscribe(' + str(id) + ')\n'))
            return self.get_ack()
        else:
            return 0


    def register(self, name):
        """ Register the client's name with the server and return the ack. """
        
        # If a registration is made then the reader needs
        # to be created if it doesn't already exist.
        if (self.reader is None):
            self.reader = Reader(self.datasock, self.callback)
        if (self.connected):
            self.datasock.send(from_str('register(' + name + ')\n'))
            ack = self.get_ack()
            if (ack != 0):
                    self.name = name 
            return ack
        else:
            return 0

    def deregister(self):
        """ Unregister the client's name with the server and return the ack. """
        
        if (self.connected):
            self.datasock.send(from_str('deregister(' + self.name + ')\n'))
            ack = self.get_ack()
            if (ack != 0):
                self.name = ''
            return ack
        else:
            return 0

    def addr2str(self, addr):
        if isinstance(addr, str):
            return addr
        assert isinstance(addr, PStruct)
        assert addr.functor.val == '@' and addr.arity() == 2
        host = addr.args[1]
        name = addr.args[0]
        if isinstance(name, PStruct):
            assert name.functor.val == ':' and name.arity() == 2
            return str(name.args[0]) + ':'+ str(name.args[1]) + '@' + str(host)
        else:
            return str(name) + '@' + str(host)

    def p2p(self, toaddr, term):
        """ Send a p2p message to the server and return the ack. """
        #print toaddr
        straddr = self.addr2str(toaddr)
        name = self.my_machine_name
        if (self.name == ''):
            return 0
        elif '@' in straddr:
            straddr = straddr.replace('localhost', "'"+name+"'")
            self.datasock.send(from_str('p2pmsg(' + straddr + ', '\
                               + self.name + "@'" + name\
                               +  "'," + str(term) + ')\n'))
            return self.get_ack()
        elif _p2p_var_addr.match(toaddr):
            self.datasock.send(from_str('p2pmsg(' + straddr \
                                   + ", " \
                                   + self.name + "@'" + name\
                                   +  "'," + str(term) + ')\n'))
            return self.get_ack()
        else:
            self.datasock.send(from_str('p2pmsg(' + straddr \
                                   + "@'" + name + "', " \
                                   + self.name + "@'" + name\
                                   +  "'," + str(term) + ')\n'))
            return self.get_ack()

    def _pop_rock(self, strn):
        """Gets the rock off of the message, returning (message_to_parse, rock)"""
        rock, message = strn.split(" ", 1)
        return (message, int(rock))

