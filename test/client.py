from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys

# This is a simple node on the network.

port = 5050

# This is a list of nodes it "Knows" exists on the network. We can probably move this into a text file in the future and
# implement it how we were discussing last week.
known_nodes = [(("127.0.0.1", 6060))]

#Logging
log.startLogging(sys.stdout)

def print_result(result):
    print("Value found=" + str(result))
    # Stops the server code from executing once it's done
    reactor.stop()

def get(result, server):
    print("Grabbing the result from the server")
    # Gets the specified key/value pair from the server, then it will call the print_result function with the retrieved
    # value
    server.get("key").addCallback(print_result)

# Simple function to call upon a server bootstrap. It will add a key/value pair to the hash table
def set(stuff, morestuff):
    print("I'm doing things!")
    # Sets a key/value pair in the DHT, then calls the get function, with the server.
    server.set("key", "value").addCallback(get, server)


# Starts setting up the local server to run
print("Setting up listening server")
server = Server()
server.listen(port)

# The addCallback can be added to many of the server functions, and can be used to chain call functions
server.bootstrap(known_nodes).addCallback(set, server)

# starts the execution of the server code
reactor.run()


