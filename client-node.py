import sys,os,socket,argparse
# Uses local version of Kademlia
sys.path.insert(0, "kademlia")
from twisted.internet import reactor, tksupport
from twisted.python import log
from kademlia.network import Server

try: #python 2
    from Tkinter import *
except ImportError: #python 3
    from tkinter import *

backup = "client_state.bak"
default_port = 5050


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
args = parser.parse_args()

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
# implement it how we were discussing last week.
known_nodes = [("127.0.0.1", 5050)]

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

ConnectionsList = []

selectedIP = NONE
chatWindow = NONE

def chatWindowPrintText(text):
    chatWindow.config(state=NORMAL)
    chatWindow.insert(END, text)
    chatWindow.config(state=DISABLED)
    chatWindow.see(END)

def updateSelected():

    global selectedIP
    #TODO make this more robust/usefull etc
    selectedIP = ConnectionsList[1].get(ACTIVE)

def refreshAvailIP():
    global IPList


    #TODO populate the list of IP addresses here
    IPList = {"Robert" : "192.168.0.1", "Mike" : "100.42.16.45"}

    #clear all the old values from the list box
    ConnectionsList[0].delete(0, END)
    ConnectionsList[1].delete(0, END)
    for item in IPList.keys():
        ConnectionsList[0].insert(END, item)
        ConnectionsList[1].insert(END, IPList.get(item))

def connectToIP():

    global selectedIP
    updateSelected()

    #TODO failure cases for ip addresses go here
    if(selectedIP == NONE or selectedIP == ""):
        chatWindowPrintText("Unable to connect to IP\n")
        return False;

    #TODO connect to selected IP here
    chatWindowPrintText("Attempting to connect to "+ selectedIP+"\n")
    return True

def closeProgram():
    reactor.stop()

def initialize():
    global ConnectionsList
    global chatWindow
    #set up the main window
    root = Tk()
    root.title("Encrypted P2P")

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

    chatWindow = Text(chatTextFrame, height=5, state=DISABLED)
    chatWindow.pack(side=LEFT, fill=BOTH)

    scrollbar.config(command=chatWindow.yview)
    chatWindow.config(yscrollcommand=scrollbar.set)

    #set up user text field for input
    textEntry = Text(root, height=1)
    textEntry.pack()


    #set up buttons and their method calls
    refreshButton = Button(root, text="Refresh List", command=refreshAvailIP)
    refreshButton.pack(side=LEFT)

    exitButton = Button(root, text="Exit Program", command=closeProgram)
    exitButton.pack(side=RIGHT)

    connectButton = Button(root, text="Connect", command=connectToIP)
    connectButton.pack(side=RIGHT)



    #listB.pack()

    return root


root = initialize()
tksupport.install(root)

# starts the execution of the server code
reactor.run()

# Anything after the run command will run after a ctrl+c is given and the server is closed gracefully
if args.log:
    l.close()
