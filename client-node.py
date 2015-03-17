import sys,os,socket,argparse
# Uses local version of Kademlia
sys.path.insert(0, "kademlia")
from twisted.internet import reactor, tksupport, task
from twisted.python import log
from kademlia.network import Server

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *

# ----------------------------------------------------------------------------------------------------------------------
# Importing and file handling section

backup = "client_state.bak"

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
# implement it how we were discussing last week.
known_nodes = []

# list boxes containing contact info
# Contacts takes the form of {"username": "sample", "key": "key_value", "ip": "1.1.1.1", "port": "3000", "online": False}
Contacts = []

# Import settings from the configuration file
import config

# This is a simple node on the network.
# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', required=True, type=str, action='store', default=False, help='Set the client port.')
parser.add_argument('-l', '--log', dest='log', type=str, action='store', default=False, help='Specify a log file to output to. Default is stdout.')
parser.add_argument('-s', '--save', dest='save', action='store_true', default=False, help='Specify whether you want to save a state')
parser.add_argument('-I', '--bsip', dest='bsip', type=str, action='store', default=False, help='Set the bootstrap server IP.')
parser.add_argument('-P', '--bsport', dest='bsport', type=str, action='store', default=False, help='Set the bootstrap server port.')
parser.add_argument('-N', '--nogui', dest='nogui', action='store_true', default=False, help='Do not run the GUI part of the node')
parser.add_argument('-c', '--client', dest='client', type=int, action='store', default=False, help='Set up the port for the client.')
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

kad_port = config.kademlia_port
if args.port:
    kad_port = args.port

client_port = 4040
if args.client:
    client_port = int(args.client)

# ----------------------------------------------------------------------------------------------------------------------
# Begin Support Code

# Sets the value of the hostname to it's IP address according to the other nodes in the network
def set(myIP, server):
    if os.path.isfile("identity.txt"):
        with open("identity.txt", "r") as f:
            for line in f:
                id = line.split()
                if len(id) == 2:
                    log.msg("Adding identity to table with username " + str(id[1]) + " and key " + str(id[0]))
                    server.set(str(id[0]) + str(id[1]), myIP)
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
server.listen(int(kad_port))

if os.path.isfile(backup):
    server.loadState(backup)

# Backup every 5 minutes
if args.save:
    if os.path.exists(backup):
        server.saveStateRegularly(backup, 300)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
server.bootstrap(known_nodes).addCallback(getIPs, server)

# ----------------------------------------------------------------------------------------------------------------------
#Begin GUI code

from twisted.internet.protocol import Factory, ClientFactory, ServerFactory, Protocol
#from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint, connectProtocol

from twisted.internet import protocol, reactor, stdio
from twisted.protocols import basic
import unicodedata

class EchoServerProtocol(basic.LineReceiver):
    def lineReceived(self, line):
        log.msg("Server Recieved: " + line)
        factory = protocol.ClientFactory()
        factory.protocol = EchoClientProtocol

        chatWindowPrintText(line)

class EchoClientProtocol(basic.LineReceiver):
    def connectionMade(self):
        self.setName("Username")

        log.msg("Client Send: " + self.name + " Connected")
        self.sendLine(self.name + " Connected\n")


    def setName(self, name):
        if self.users.has_key(name) or name.lower() == 'server':
            self.sendLine('That username is in use!\r\nUsername: ')
            self.setName(str(name+'*'))
        elif ' ' in name:
            self.sendLine('No spaces are allowed in usernames!\r\nUsername: ')
        elif name == '':
            self.sendLine('You must enter a username!\r\nUsername: ')
        else:
            self.users[name] = self
            self.name = name

    def sendMessage(self, text):
        #log.msg("Client Send: "+text)

        #Send line does not allow unicode strings, so we convert it before sending
        normalized = unicodedata.normalize('NFKD', text).encode('ascii','ignore')
        self.sendLine(self.name + ": " + normalized)

    def __init__(self,addr=None,users=None):
        self.name = None
        self.addr = addr
        self.users = users

class ClientFactory(Factory):
    protocol = EchoClientProtocol

    def startedConnecting(self, connector):
        log.msg("ClientFactory: Starting to connect")

    def buildProtocol(self, addr):
        log.msg("ClientFactory: build Protocol")
        return EchoClientProtocol(addr=addr,users=self.users)

    def clientConnectionLost(self, connector, reason):
        log.msg("ClientFactory: Connection Lost")
    def clientConnectionFailed(self, connector, reason):
        log.msg("ClientFactory: Connection Failed")

    def __init__(self):
        self.users = {}
        self.name = None

# list boxes in GUI for displaying and selecting contact info
ConnectionsList = []

selectedIP = NONE
chatWindow = NONE
textEntry = NONE

clientFactory = NONE

# print givent text in the chat text window
def chatWindowPrintText(text):
    chatWindow.config(state=NORMAL)
    chatWindow.insert(END, text)
    chatWindow.config(state=DISABLED)
    chatWindow.see(END)

# Hopefully temp way to clean up the newline in the text box after sending messages
def clearText(event):
    if event.keysym == 'Return':
        textEntry.delete('0.0', END)

#Send a message through the GUI chat
def sendChatMessage(event):
    global textEntry
    global clientFactory

    if event.keysym == 'Return':
        message = textEntry.get('0.0', END)
        textEntry.delete('0.0', END)

        message = message.lstrip()
        chatWindowPrintText(message)

        #Send the message to other users
        if clientFactory is not NONE:
            for name in clientFactory.users:
                #TODO avoid sending the message to ourselves
                clientFactory.users[name].sendMessage(message)


# update the global selected IP address
def updateSelected():

    global selectedIP
    #TODO make this more robust/usefull etc
    selectedIP = ConnectionsList[1].get(ACTIVE)


# Takes the result from the DHT and parses out the IP and port
# TODO: This will have to be modified when we have to resolve multiple IP/PORT pairs for NAT etc.
def get_contact_location(result, contact):
    if result is not None:
        contact['ip'] = result[0][0]
        contact['port'] = result[0][1]

# Refreshes the IPs of all of the contacts. Because of async nature of Twisted, this may not show right away.
def refreshAvailIP():
    global Contacts
    log.msg("Refreshing Contact List automagically")
    for contact in Contacts:
        # This adds the get_ip function to the server callback list. Will do so for each contact
        server.get(contact['key'] + contact['username']).addCallback(get_contact_location, contact)
    #print(Contacts)

    #clear the listboxes in the GUI of old values
    ConnectionsList[0].delete(0, END)
    ConnectionsList[1].delete(0, END)

    # add the new values to the GUI
    ConnectionsList[0].insert(END, contact['username'])
    ConnectionsList[1].insert(END, contact['ip'])


# connect to the selected IP address
def connectToIP():

    global selectedIP
    global clientService, clientFactory
    updateSelected()

    #TODO failure cases for ip addresses go here
    if(selectedIP == NONE or selectedIP == ""):
        chatWindowPrintText("Unable to connect to IP\n")
        return False

    chatWindowPrintText("Attempting to connect to "+ selectedIP+"\n")

    #TODO make unbroken (might be doing multiple connects to same IP etc.)
    if clientFactory is NONE:
        clientFactory = ClientFactory()
    #TODO don't use localhost(change when we have populated IP list)
    #TODO don't use fixed port
    reactor.connectTCP('localhost', 9000, clientFactory)

    return True

def closeProgram():
    reactor.stop()

#Set up the GUI and containers, frames, lists, etc. before running the program loop
def initializeGUI():
    global ConnectionsList
    global chatWindow
    global textEntry
    #set up the main window
    root = Tk()
    root.title("Encrypted P2P Chat GUI")
    root.protocol('WM_DELETE_WINDOW', closeProgram)

    mainFrame = Frame(root)
    mainFrame.pack()

    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))
    ConnectionsList.append(Listbox(mainFrame, selectmode=SINGLE))

    ConnectionsList[0].grid(row=0, column=0)
    ConnectionsList[1].grid(row=0, column=1)

    #set up chat window with scroll bar
    chatTextFrame = Frame(root)
    chatTextFrame.pack()

    scrollbar = Scrollbar(chatTextFrame)
    scrollbar.pack(side=RIGHT, fill=Y)

    chatWindow = Text(chatTextFrame, height=8, state=DISABLED)
    chatWindow.pack(side=LEFT, fill=BOTH)

    scrollbar.config(command=chatWindow.yview)
    chatWindow.config(yscrollcommand=scrollbar.set)

    #set up user text field for input
    chatEntryFrame = Frame(root)
    chatEntryFrame.pack()

    textEntry = Text(chatEntryFrame, height=2)
    textEntry.pack(side=LEFT)
    textEntry.bind("<Key>", sendChatMessage)
    textEntry.bind("<KeyRelease>", clearText)


    #set up buttons and their method calls
    refreshButton = Button(root, text="Refresh List", command=refreshAvailIP)
    refreshButton.pack(side=LEFT)

    exitButton = Button(root, text="Exit Program", command=closeProgram)
    exitButton.pack(side=RIGHT)

    connectButton = Button(root, text="Connect", command=connectToIP)
    connectButton.pack(side=RIGHT)

    return root

#start a server for the chat service and GUI
factory = protocol.ServerFactory()
factory.protocol = EchoServerProtocol
try:
    reactor.listenTCP(client_port, factory)
except: #won't break absolutly everything if you run two instances on one machine
    log.err("Error starting Chat Server: port in use")

#set up the gui root and connect it to the reactor
if not args.nogui:
    root = initializeGUI()
    tksupport.install(root)

#Will automatically refresh the contacts every minute
if args.refresh:
    contact_refresh_loop = task.LoopingCall(refreshAvailIP)
    contact_refresh_loop.start(10)

# starts the execution of the server code
reactor.run()

# Anything after the run command will run after a ctrl+c is given and the server is closed gracefully
if args.log:
    l.close()
