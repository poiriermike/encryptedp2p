import sys, os
# Uses local version of Kademlia
sys.path.insert(0,"../kademlia")
from twisted.internet import reactor
from twisted.python import log
from kademlia.network import Server
import argparse

# This is a really simple dedicated server. It will start on the specified port, load state variables from a file, and
# save them intermittently.

backup = "serverfiles/state.bak"

# Some fancy argument parsing. cause I'm cool like that.
parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port', dest='port', type=int, required=True, action='store', help='Port to start the server on. Defaults to 6060.')
parser.add_argument('-l', '--log', dest='log', type=str, action='store', default=False, help='Specify a log file to output to. Default is stdout.')
args = parser.parse_args()


# Logging and fun stuff like that
if args.log:
    # NOTE: This works, however I am unsure if the logging function will close the file descriptor when the server finishes.
    l = open(args.log, "a")
    log.startLogging(l)
else:
    log.startLogging(sys.stdout)

print("Setting up listening server")
server = Server()
server.listen(args.port)

# This is a backup
if os.path.isfile(backup):
    server.loadState(backup)

# Saves to a backup every 5 minutes
#TODO: This should be changed to create the directory and file instead
if os.path.exists(backup):
server.saveStateRegularly(backup, 300)


reactor.run()
