import sys,os,socket,argparse
# Uses local version of Kademlia
sys.path.insert(0, "kademlia")
from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server


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
known_nodes = [(("127.0.0.1", 5050))]

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
    # NOTE: This works, however I am unsure if the logging function will close the file descriptor when the server finishes.
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

# Backup every 5 minutes
#TODO: This should be changed to create the directory and file instead
if args.save:
    if os.path.exists(backup):
        server.saveStateRegularly(backup, 300)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
server.bootstrap(known_nodes).addCallback(getIPs, server)

# starts the execution of the server code
reactor.run()

# Anything after the run command will run after a ctrl+c is given and the server is closed gracefully

if args.log:
    l.close()
