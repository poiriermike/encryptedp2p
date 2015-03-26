from collections import Counter

from kademlia.log import Logger
from kademlia.utils import deferredDict
from kademlia.node import Node, NodeHeap


class SpiderCrawl(object):
    """
    Crawl the network and look for given 160-bit keys.
    """
    def __init__(self, protocol, node, peers, ksize, alpha):
        """
        Create a new C{SpiderCrawl}er.

        Args:
            protocol: A :class:`~kademlia.protocol.KademliaProtocol` instance.
            node: A :class:`~kademlia.node.Node` representing the key we're looking for
            peers: A list of :class:`~kademlia.node.Node` instances that provide the entry point for the network
            ksize: The value for k based on the paper
            alpha: The value for alpha based on the paper
        """
        self.protocol = protocol
        self.ksize = ksize
        self.alpha = alpha
        self.node = node
        self.nearest = NodeHeap(self.node, self.ksize)
        self.lastIDsCrawled = []
        self.log = Logger(system=self)
        self.log.info("creating spider with peers: %s" % peers)
        self.nearest.push(peers)


    def _find(self, rpcmethod, localValue=None):
        """
        Get either a value or list of nodes.

        Args:
            rpcmethod: The protocol's callfindValue or callFindNode.

        The process:
          1. calls find_* to current ALPHA nearest not already queried nodes,
             adding results to current nearest list of k nodes.
          2. current nearest list needs to keep track of who has been queried already
             sort by nearest, keep KSIZE
          3. if list is same as last time, next call should be to everyone not
             yet queried
          4. repeat, unless nearest list has all been queried, then ur done
        """
        self.log.info("crawling with nearest: %s" % str(tuple(self.nearest)))
        count = self.alpha
        if self.nearest.getIDs() == self.lastIDsCrawled:
            self.log.info("last iteration same as current - checking all in list now")
            count = len(self.nearest)
        self.lastIDsCrawled = self.nearest.getIDs()

        ds = {}
        for peer in self.nearest.getUncontacted()[:count]:
            ds[peer.id] = rpcmethod(peer, self.node)
            self.nearest.markContacted(peer)
        if localValue:
            return deferredDict(ds).addCallback(self._nodesFound, localValue)
        else:
            return deferredDict(ds).addCallback(self._nodesFound)


class ValueSpiderCrawl(SpiderCrawl):
    def __init__(self, protocol, node, peers, ksize, alpha, encryption_key, server):
        SpiderCrawl.__init__(self, protocol, node, peers, ksize, alpha)
        # keep track of the single nearest node without value - per
        # section 2.3 so we can set the key there if found
        self.nearestWithoutValue = NodeHeap(self.node, 1)
        self.encryption_key = encryption_key
        self.server = server

    def find(self, localValue=None):
        """
        Find either the closest nodes or the value requested.
        """
        return self._find(self.protocol.callFindValue, localValue)

    def _nodesFound(self, responses, localValue=None):
        """
        Handle the result of an iteration in _find.
        """
        toremove = []
        foundValues = []
        if localValue:
            self.log.debug("Local value is %s" % str(localValue))
            foundValues.append(localValue)
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            elif response.hasValue():
                foundValues.append(response.getValue())
            else:
                peer = self.nearest.getNodeById(peerid)
                self.nearestWithoutValue.push(peer)
                self.nearest.push(response.getNodeList())
        self.nearest.remove(toremove)

        if len(foundValues) > 0:
            return self._handleFoundValues(foundValues)
        if self.nearest.allBeenContacted():
            # not found!
            return None
        return self.find()

    def _handleFoundValues(self, values):
        """
        We got some values!  Exciting.  But let's make sure
        they're all the same or freak out a little bit.  Also,
        make sure we tell the nearest node that *didn't* have
        the value to store it.
        """

        self.log.debug("Handling found values")

        filtered_values = []
        for x in values:
            self.log.debug("x:" + str(x))
            self.log.debug(type(x[1]))
            if self.encryption_key is None:
                temp_encryption_key = x[0]
            else:
                temp_encryption_key = self.encryption_key
            if self.server.evaluate_timestamp(x[1], temp_encryption_key) is not None:
                filtered_values.append((x, temp_encryption_key))

        valueCounts = Counter([x[0] for x in values])
        if len(valueCounts) != 1:
            args = (self.node.long_id, str(values))
            self.log.warning("Got multiple values for key %i: %s" % args)

        sorted_values = sorted(filtered_values, key=lambda y: self.server.evaluate_timestamp(y[0][1], y[1]))[-1:]
        value = None
        if sorted_values is not None:
            value = sorted_values[-1][0]
        #value = valueCounts.most_common(1)[0][0]

        self.log.debug("Backing up values to nearest neighbour")

        peerToSaveTo = self.nearestWithoutValue.popleft()
        if peerToSaveTo is not None and value is not None:
            d = self.protocol.callStore(peerToSaveTo, self.node.id, value, self.encryption_key is None)
            return d.addCallback(lambda _: value)
        self.log.debug("Found %s" % value)
        return value


class NodeSpiderCrawl(SpiderCrawl):
    def find(self):
        """
        Find the closest nodes.
        """
        return self._find(self.protocol.callFindNode)

    def _nodesFound(self, responses):
        """
        Handle the result of an iteration in _find.
        """
        toremove = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            else:
                self.nearest.push(response.getNodeList())
        self.nearest.remove(toremove)

        if self.nearest.allBeenContacted():
            return list(self.nearest)
        return self.find()


class RPCFindResponse(object):
    def __init__(self, response):
        """
        A wrapper for the result of a RPC find.

        Args:
            response: This will be a tuple of (<response received>, <value>)
                      where <value> will be a list of tuples if not found or
                      a dictionary of {'value': v} where v is the value desired
        """
        self.response = response

    def happened(self):
        """
        Did the other host actually respond?
        """
        return self.response[0]

    def hasValue(self):
        return isinstance(self.response[1], dict)

    def getValue(self):
        return self.response[1]['value']

    def getNodeList(self):
        """
        Get the node list in the response.  If there's no value, this should
        be set.
        """
        nodelist = self.response[1] or []
        return [Node(*nodeple) for nodeple in nodelist]
