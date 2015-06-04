import sys,os,socket,argparse
# Uses local version of Kademlia
sys.path.insert(0, "kademlia")
from twisted.internet import reactor, tksupport, task
from twisted.python import log
from twisted.internet.task import LoopingCall
from kademlia.network import Server

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *

# ----------------------------------------------------------------------------------------------------------------------
# Importing and file handling section

backup = "client_state.bak"

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
known_nodes = []

# Contacts takes the form of {"username": "sample", "key": "key_value", "ip": "1.1.1.1", "port": "3000", "online": False}
Contacts = []

# Import settings from the configuration file
import config

# This is a simple node on the network.
# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', type=str, action='store', default=False, help='Set the application''s port. Overrides the config file.')
parser.add_argument('-l', '--log', dest='log', type=str, action='store', default=False, help='Specify a log file to output to. Default is stdout.')
parser.add_argument('-s', '--save', dest='save', action='store_true', default=False, help='Specify whether you want to save a state. Overrides the config file.')
parser.add_argument('-I', '--bsip', dest='bsip', type=str, action='store', default=False, help='Set the bootstrap server IP. Overrides the config file.')
parser.add_argument('-P', '--bsport', dest='bsport', type=str, action='store', default=False, help='Set the bootstrap server port. Overrides the config file.')
parser.add_argument('-N', '--nogui', dest='nogui', action='store_true', default=False, help='Do not run the GUI part of the node')
parser.add_argument('-r', '--refresh', dest='refresh', action='store_true', default=False, help='Automatically refresh the contact list.')
args = parser.parse_args()

# Import the contacts from the contact file
if os.path.isfile(config.contacts_file):
    with open(config.contacts_file, "r") as f:
        for line in f:
            info = line.split()
            if len(info) != 0:
                Contacts.append({"username": info[1], "key": info[0], "ip": None, "port": None, "online": False})
else:
    with open(config.contacts_file, "w"):
        log.msg("No contacts found. Adding contact file.")

# Set up the Kademlia bootstrapping
if (args.bsip and not args.bsport) or (not args.bsip and args.bsport):
    log.err("Error. Missing ip or port argument")
    exit(1)
elif not args.bsip and not args.bsport:
    if os.path.isfile(config.bootstrap_file):
        with open(config.bootstrap_file, "r") as f:
            for line in f:
                bsid = line.split()
                if len(bsid) != 2 or len(bsid) != 0:
                    log.err("Line not formatted correctly. Ignoring.")
                elif len(bsid) == 2:
                    known_nodes.append([bsid[0], bsid[1]])
else:
    log.msg("Bootstrapping IP " + args.bsip + " and port " + args.bsport)
    known_nodes = [(args.bsip, int(args.bsport))]

#Logging
if args.log:
    l = open(args.log, "a")
    log.startLogging(l)
else:
    log.startLogging(sys.stdout)

port = int(config.port)
if args.port:
    port = int(args.port)

# ----------------------------------------------------------------------------------------------------------------------
# Begin Support Code
username = "Mikesucks"

# Sets the value of the hostname to it's IP address according to the other nodes in the network
def set(myIP, server):
    global username
    if os.path.isfile("identity.txt"):
        with open("identity.txt", "r") as f:
            for line in f:
                id = line.split()
                if len(id) == 2:
                    log.msg("Adding identity to table with username " + str(id[1]) + " and key " + str(id[0]))
                    if myIP != []:
                        myIP[0] = list(myIP[0])
                    #myIP[0][1] = port
                    # server.set(str(id[0]) + str(id[1]), myIP)
                    # TODO: Figure out how we want to store keys! These are just hard coded right now, the
                    #   same for every user.
                    server.setContactInfo(str(id[0]) + str(id[1]), myIP, str(id[0]), "public_key")
                    username = str(id[1])
                    gui.set_username(username) #update the username in the gui
                else:
                    log.err("Error adding identity file.")
                    reactor.stop()
    else:
        log.err("No identity fie found. Exiting.")
        reactor.stop()

# Simple function to call upon a server bootstrap. It will add a key/value pair to the hash table
def getIPs(stuff, morestuff):
    # This will grab a of what the node's IP looks at from the outside, and then adds it to the DHT
    # One thing we need to look into is figuring out what the port is to get past NAT.
    server.inetVisibleIP().addCallback(set, server)

# Starts setting up the local server to run
log.msg("Setting up listening server")
server = Server()
server.listen(int(port))

if os.path.isfile(backup):
    server.loadState(backup)

# Backup every 5 minutes
if args.save:
    if os.path.exists(backup):
        server.saveStateRegularly(backup, 300)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
#server.bootstrap(known_nodes).addCallback(getIPs, server)


def setContactInfo():
    return server.bootstrap(known_nodes).addCallback(getIPs, server)

updateInfo = task.LoopingCall(setContactInfo)
updateInfo.start(300)

# ----------------------------------------------------------------------------------------------------------------------
#Begin GUI code

from clientgui import client_gui

gui = client_gui(reactor, log, server, Contacts)
gui.set_username(username)

#set up the gui root and connect it to the reactor
if not args.nogui:
    root = gui.initializeGUI()
    tksupport.install(root)

# --------- gui interaction --------

# update gui when new message received
def pollForMessage():
    messages = server.pollReceivedMessages()

    if messages is None:
        return

    for message in messages:
        if message != "":
            log.msg("Server Recieved: " + message)
            gui.chatWindowPrintText(message)

#Will automatically refresh the contacts every minute
if args.refresh:
    contact_refresh_loop = task.LoopingCall(refreshAvailIP)
    contact_refresh_loop.start(10)

message_polling_loop = task.LoopingCall(pollForMessage)
message_polling_loop.start(1)

# starts the execution of the server code
reactor.run()

# Anything after the run command will run after a ctrl+c is given and the server is closed gracefully
if args.log:
    l.close()
