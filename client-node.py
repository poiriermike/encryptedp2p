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

backup = "client_state.bak"
default_port = 5050

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
# implement it how we were discussing last week.
known_nodes = [("127.0.0.1", 5050)]

# list boxes containing contact info
Contacts = [{"username": "sample", "key": "key_value", "ip": "1.1.1.1", "port": "3000", "online": False}]

# This is a simple node on the network.
# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', required=True, type=str, action='store', default=False, help='Set the client port.')
parser.add_argument('-f', '--file', dest='file', type=str, action='store', help='File with a list of known hosts.')
parser.add_argument('-l', '--log', dest='log', type=str, action='store', default=False, help='Specify a log file to output to. Default is stdout.')
parser.add_argument('-b', '--bootstrap', dest='bootstrap', action='store_true', default=False, help='Set this flag if the you want to specify a bootstrap IP and port')
parser.add_argument('-s', '--save', dest='save', action='store_true', default=False, help='Specify whether you want to save a state')
parser.add_argument('-I', '--bsip', dest='bsip', type=str, action='store', default=False, help='Set the bootstrap server IP.')
parser.add_argument('-P', '--bsport', dest='bsport', type=str, action='store', default=False, help='Set the bootstrap server port.')
parser.add_argument('-N', '--nogui', dest='nogui', action='store_true', default=False, help='Do not run the GUI part of the node')
args = parser.parse_args()

# Import the contacts from the contact file
# TODO: Consider making the contact file settable from the command line
if os.path.isfile("contacts.txt"):
    with open("contacts.txt", "r") as f:
        for line in f:
            info = line.split()
            if len(info) != 0:
                Contacts.append({"username": info[1], "key": info[0], "ip":None, "port": None, "online": False})
else:
    with open("contacts.txt", "w"):
        log.msg("No contacts found. Adding contact file.")

if args.bootstrap:
    if not args.bsip or not args.bsport:
        print("Error. Missing ip or port argument")
        exit(1)
    # This should be a log. Once I figure out how to
    print("Bootstrapping IP " + args.bsip + " and port " + args.bsport)
    known_nodes = [(args.bsip, int(args.bsport))]
else:
    if args.bsip or args.bsport:
        print("Warning. The values for IP and port input will not be taken unless the -b flag is set")

if args.file:
    if os.path.isfile(args.file):
        known_nodes = []
        with open(args.file, "r") as f:
            for line in f:
                l = line.split()
                if len(l) == 2:
                    known_nodes.append((l[0], int(default_port)))
                elif len(l) == 1:
                    known_nodes.append((l[0], int(l[1])))
                else:
                    print("Warning. '" + line + "' is not a valid ip/port pair")

#Logging
# Logging and fun stuff like that
if args.log:
    l = open(args.log, "a")
    log.startLogging(l)
else:
    log.startLogging(sys.stdout)

'''
def print_result(result):
    print("Value found=" + str(result))

def get(result, server):
    print("Grabbing the result from the server")
    # Gets the specified key/value pair from the server, then it will call the print_result function with the retrieved
    # value
    server.get(socket.gethostname()).addCallback(print_result)

# Sets the value of the hostname to it's IP address according to the other nodes in the network
def set(stuff, server):
    print("STUFF " + str(stuff))
    server.set(socket.gethostname(), stuff).addCallback(get, server)
'''

#---------------------------------------------------------------------------------------------------------------------
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
print("Setting up listening server")
server = Server()
server.listen(int(args.port))

if os.path.isfile(backup):
    server.loadState(backup)

if args.save:
    # Backup every 5 minutes
    if os.path.exists(backup):
        server.saveStateRegularly(backup, 300)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
server.bootstrap(known_nodes).addCallback(getIPs, server)

#----------------------------------------------------------------------------------------------------------------------
#Begin GUI code

from twisted.internet.protocol import Factory, ClientFactory, ServerFactory, Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, TCP4ServerEndpoint, connectProtocol
from sys import stdout

# Simple Server recieve protocol. writes data to GUI
class EchoServer(Protocol):
    def dataRecieved(selfself, data):
        print("Echo Server: data recieved: " + data)
        chatWindowPrintText(data)

class ServerFactory(ServerFactory):
    protocol = EchoServer

    def buildProtocol(self, addr):
        print("Echo Server: build protocol")
        return EchoServer()

# Set up server listening skills
#endpoint = TCP4ServerEndpoint(reactor, 9000)
#endpoint.listen(ServerFactory())

s = ServerFactory()
try:
    reactor.listenTCP(9000, s)
except:
    pass #reactor.listenTCP(9010, s)

class EchoClient(Protocol):
    def makeConnection(self, transport):
        print("Echo Client: make Connection")

    def sendMessage(self, text):
        print("Echo Client: called sendMessage")
        #self.transport.write(text)

class ClientFactory(ClientFactory):
    protocol = EchoClient

    def startConnecting(self, connector):
        print("ClientFactory: Starting to connect")

    def buildProtocol(self, addr):
        print("ClientFactory: build Protocol")
        s = EchoClient()
        s.factory = self

        return s

    def clientConnectionLost(self, connector, reason):
        print("ClientFactory: Connection Lost")
    def clientConnectionFailed(self, connector, reason):
        print("ClientFactory: Connection Failed")

# list boxes containing contact info
ConnectionsList = []

selectedIP = NONE
chatWindow = NONE
textEntry = NONE

clientFactory = NONE
clientService = NONE

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
    if event.keysym == 'Return':
        message = textEntry.get('0.0', END)
        textEntry.delete('0.0', END)

        chatWindowPrintText(message.lstrip())
        #TODO send message to connected parties in chat
        if clientService is not NONE:
            clientService.sendMessage(message)


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

    #TODO connect to selected IP here
    chatWindowPrintText("Attempting to connect to "+ selectedIP+"\n")

    if clientFactory is NONE or clientService is NONE:
        clientFactory = ClientFactory()
        clientService = EchoClient()
    reactor.connectTCP('localhost', 9000, clientFactory)
    clientService.sendMessage("Connected?")
        #point = TCP4ClientEndpoint(reactor, selectedIP, 5051)
        #d = connectProtocol(point, clientService)
        #d.addCallback(gotProtocol)

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



    #listB.pack()

    return root

#set up the gui root and connect it to the reactor
if not args.nogui:
    root = initializeGUI()
    tksupport.install(root)

#Will automatically refresh the contacts every minute
#TODO uncomment this
#contact_refresh_loop = task.LoopingCall(refreshAvailIP)
#contact_refresh_loop.start(10)

# starts the execution of the server code
reactor.run()

# Anything after the run command will run after a ctrl+c is given and the server is closed gracefully
if args.log:
    l.close()
