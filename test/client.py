from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys,os,socket,argparse

# This is a simple node on the network.

port = 5050

# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', dest='file', type=str, required=True, action='store', help='File with a list of known hosts.')

args = parser.parse_args()

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
# implement it how we were discussing last week.
known_nodes = [(("10.0.0.238", 6060))]

if os.path.isfile(args.file):
    known_nodes = []
    with open(args.file, "r") as f:
        for line in f:
            known_nodes.append((line.split()[0], port))


backup = "clientfiles/state.bak"

#Logging
log.startLogging(sys.stdout)

def print_result(result):
    print("Value found=" + str(result))
    # Stops the server code from executing once it's done
    print ("Neighbours: " + str(server.bootstrappableNeighbors()))

def get(result, server):
    print("Grabbing the result from the server")
    # Gets the specified key/value pair from the server, then it will call the print_result function with the retrieved
    # value
    server.get(socket.gethostname()).addCallback(print_result)

# Simple function to call upon a server bootstrap. It will add a key/value pair to the hash table
def set(stuff, morestuff):
    print("I'm doing things!")
    # Sets a key/value pair in the DHT, then calls the get function, with the server.
    server.set(socket.gethostname(), socket.gethostname()).addCallback(get, server)


# Starts setting up the local server to run
print("Setting up listening server")
server = Server()
server.listen(port)

if os.path.isfile(backup):
    server.loadState(backup)
# Backup every 5 minutes
server.saveStateRegularly(backup, 300)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
server.bootstrap(known_nodes).addCallback(set, server)

# starts the execution of the server code
reactor.run()

