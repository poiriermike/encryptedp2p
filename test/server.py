from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import sys, os
import argparse

# This is a really simple dedicated server. It will start on the specified port, load state variables from a file, and
# save them intermittently.

# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', type=int, required=True, action='store', help='Port to start the server on. Defaults to 6060.')

args = parser.parse_args()


# Logging and fun stuff like that
log.startLogging(sys.stdout)

print("Setting up listening server")
server = Server()
server.listen(args.port)

# This is a backup
if os.path.isfile("serverfiles/state.bak"):
    server.loadState("serverfiles/state.bak")

# Saves to a backup every 5 minutes
server.saveStateRegularly("serverfiles/state.bak", 300)


reactor.run()
