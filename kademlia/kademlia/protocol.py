import random

from twisted.internet import defer

from rpcudp.protocol import RPCProtocol

from kademlia.node import Node
from kademlia.routing import RoutingTable
from kademlia.log import Logger
from kademlia.utils import digest

from simplecrypt import encrypt, decrypt, DecryptionException

def decodeTimestamp(encodedTimestamp, key):
    if not encodedTimestamp or not key:
        return None
    try:
        return int(decrypt(key, encodedTimestamp))
    except (DecryptionException, ValueError):
        return None

def encodeTimestamp(timestamp, key):
    print(str(timestamp) + str(type(timestamp)) + str(key) + str(type(key)))
    if not timestamp or not key:
        return None
    try:
        return encrypt(key, str(timestamp))
    except DecryptionException:
        return None


class KademliaProtocol(RPCProtocol):
    def __init__(self, sourceNode, storage, ksize):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)
        self.messages = []

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def getMessages(self):
        if len(self.messages) == 0:
            return None

        newList = []
	while len(self.messages) > 0:
            newList.append(self.messages.pop(0))
        return newList

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        return self.sourceNode.id

    def rpc_store(self, sender, nodeid, key, value):
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        #Check if the timestamp of any existing value is larger than the new one.
        existingValue = self.storage.get(key, None)
        if existingValue:
            if existingValue[4] < value[4]:
                existingTimestamp = decodeTimestamp(existingValue[1], value[2])
            else:
                self.log.debug("Local val unencrypted is too small")
                return True
        if (not existingValue) or (existingTimestamp < decodeTimestamp(value[1], value[2])):
            self.log.debug("got a store request from %s, storing value" % str(sender))
            self.storage[key] = value
            return True
        else:
            self.log.debug("IGNORING a store request from %s, existing timestamp %s is larger than new %s" % (str(sender), str(existingTimestamp), str(newTimestamp)))
            return True

    def rpc_send(self, sender, message):
        self.log.info("Received message: \"" + message.strip("\n") + "\" from address " + str(sender))
        self.messages.append(message)
        return True

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        node = Node(key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        value = self.storage.get(key, None)
        if value is None:
            return self.rpc_find_node(sender, nodeid, key)
        return { 'value': value }

    def callFindNode(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_node(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callFindValue(self, nodeToAsk, nodeToFind):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.find_value(address, self.sourceNode.id, nodeToFind.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callPing(self, nodeToAsk):
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.ping(address, self.sourceNode.id)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callStore(self, nodeToAsk, key, value):
        self.log.debug("Storing on %s" % str(nodeToAsk))
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceNode.id, key, value)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

    def callSend(self, message, addr, port):
        address = (addr, port)
	self.log.info("Sending message: \"" + message.strip("\n") + "\" to address " + str(address))
	self.send(address, message)

    def transferKeyValues(self, node):
        """
        Given a new node, send it all the keys/values it should be storing.

        @param node: A new node that just joined (or that we just found out
        about).

        Process:
        For each key in storage, get k closest nodes.  If newnode is closer
        than the furtherst in that list, and the node for this server
        is closer than the closest in that list, then store the key/value
        on the new node (per section 2.5 of the paper)
        """
        ds = []
        for key, value in self.storage.iteritems():
            keynode = Node(digest(key))
            neighbors = self.router.findNeighbors(keynode)
            if len(neighbors) > 0:
                newNodeClose = node.distanceTo(keynode) < neighbors[-1].distanceTo(keynode)
                thisNodeClosest = self.sourceNode.distanceTo(keynode) < neighbors[0].distanceTo(keynode)
            if len(neighbors) == 0 or (newNodeClose and thisNodeClosest):
                ds.append(self.callStore(node, key, value))
        return defer.gatherResults(ds)

    def handleCallResponse(self, result, node):
        """
        If we get a response, add the node to the routing table.  If
        we get no response, make sure it's removed from the routing table.
        """
        if result[0]:
            self.log.debug("Result is %s" % str(result))
            self.log.info("got response from %s, adding to router" % node)
            self.router.addContact(node)
            if self.router.isNewNode(node):
                self.transferKeyValues(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result
