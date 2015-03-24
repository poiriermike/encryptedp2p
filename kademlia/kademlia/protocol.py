import random
from collections import namedtuple

from twisted.internet import defer

from rpcudp.protocol import RPCProtocol

from kademlia.node import Node
from kademlia.routing import RoutingTable
from kademlia.log import Logger
from kademlia.utils import digest


class KademliaProtocol(RPCProtocol):
    def __init__(self, sourceNode, storage, ksize, server):
        RPCProtocol.__init__(self)
        self.router = RoutingTable(self, ksize, sourceNode)
        self.server = server
        self.storage = storage
        self.sourceNode = sourceNode
        self.log = Logger(system=self)

    def getRefreshIDs(self):
        """
        Get ids to search for to keep old buckets up to date.
        """
        ids = []
        for bucket in self.router.getLonelyBuckets():
            ids.append(random.randint(*bucket.range))
        return ids

    def rpc_stun(self, sender):
        return sender

    def rpc_ping(self, sender, nodeid):
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        return self.sourceNode.id

    def _finish_store(self, expected_encryption_key, sender, key, value):
        self.log.debug ("Finishing store of value (%s)" % value)
        existingValue = self.storage.get(key, None)
        new_timestamp = self.server.evaluate_timestamp(value[1], expected_encryption_key)
        self.log.debug("Decoded timestamp is %s" % str(new_timestamp))
        current_timestamp = None
        if existingValue:
            current_timestamp = self.server.evaluate_timestamp(existingValue[1], expected_encryption_key)

        if new_timestamp is None:
            self.log.debug("IGNORING a store request from %s, could not decode a timestamp" % (str(sender)))
            return False

        if (not current_timestamp) or (current_timestamp < new_timestamp):
            self.log.debug("got a store request from %s, storing value" % str(sender))
            self.storage[key] = value
            return True
        else:
            self.log.debug("IGNORING a store request from %s, existing timestamp %s is larger than new %s" % (str(sender), str(existingValue[1]), str(value[1])))
            return False

    def rpc_store(self, sender, nodeid, key, value, is_self_signed=False):
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)

        # Find the encryption key to use, if one exists
        if not is_self_signed:
            self.log.debug("Storing encrypted value (%s=%s), looking up encryption key" % (key, value))
            # self.log.debug("############Hello")
            # self.server.get(value[2], True)
            # self.log.debug("############End Test")
            d = defer.maybeDeferred(self.server.get, value[2], True)
            return d.addCallback(self._finish_store, sender, key, value)
        else:
            self.log.debug("Storing self signed value (key=%i, value=%s)" % (long(key.encode('hex'), 16), str(value)))
            return self._finish_store(value[0], sender, key, value)

    def rpc_find_node(self, sender, nodeid, key):
        self.log.info("finding neighbors of %i in local table" % long(nodeid.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        node = Node(key)
        return map(tuple, self.router.findNeighbors(node, exclude=source))

    def rpc_find_value(self, sender, nodeid, key):
        self.log.debug("_____________________ Finding value at %i!" % long(key.encode('hex'), 16))
        source = Node(nodeid, sender[0], sender[1])
        self.router.addContact(source)
        value = self.storage.get(key, None)
        self.log.debug("_____________________ Found in local storage: %s" % str(value))
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

    def callStore(self, nodeToAsk, key, value, isSelfSigned):
        self.log.debug("callStore: key:%s, value:%s, selfSigned?:%s" % (key, value, str(isSelfSigned)))
        address = (nodeToAsk.ip, nodeToAsk.port)
        d = self.store(address, self.sourceNode.id, key, value, isSelfSigned)
        return d.addCallback(self.handleCallResponse, nodeToAsk)

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
            self.log.info("got response from %s, adding to router" % node)
            self.log.info("Response: (%s)" % str(result))
            self.router.addContact(node)
            if self.router.isNewNode(node):
                self.transferKeyValues(node)
        else:
            self.log.debug("no response from %s, removing from router" % node)
            self.router.removeContact(node)
        return result
