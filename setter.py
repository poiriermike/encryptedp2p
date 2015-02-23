from twisted.internet import reactor
from twisted.python import log
import sys
sys.path.insert(0, "kademlia")
from kademlia.network import Server

log.startLogging(sys.stdout)

if len(sys.argv) != 5:
    print "Usage: python query.py <bootstrap ip> <bootstrap port> <key>"
    sys.exit(1)

ip = sys.argv[1]
port = int(sys.argv[2])
key = sys.argv[3]
value = sys.argv[4]

print "Getting %s (with bootstrap %s:%i)" % (key, ip, port)

def done(result):
    reactor.stop()

def bootstrapDone(found, server, key):
    if len(found) == 0:
        print "Could not connect to the bootstrap server."
        reactor.stop()
    server.set(key, value).addCallback(done)

server = Server()
server.listen(port-2)
server.bootstrap([(ip, port)]).addCallback(bootstrapDone, server, key)

reactor.run()