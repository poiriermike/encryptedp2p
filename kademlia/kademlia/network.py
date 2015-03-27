"""
Package for interacting on the network at a high level.
"""
import random
import pickle

from twisted.internet.task import LoopingCall
from twisted.internet import defer, reactor, task

from kademlia.log import Logger
from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict, digest
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node
from kademlia.crawling import ValueSpiderCrawl
from kademlia.crawling import NodeSpiderCrawl
from protocol import decodeTimestamp
from protocol import encodeTimestamp

import datetime

from simplecrypt import encrypt, decrypt, DecryptionException

class Server(object):
    """
    High level view of a node instance.  This is the object that should be created
    to start listening as an active node on the network.
    """

    def __init__(self, ksize=20, alpha=3, id=None, storage=None):
        """
        Create a server instance.  This will start listening on the given port.

        Args:
            ksize (int): The k parameter from the paper
            alpha (int): The alpha parameter from the paper
            id: The id for this node on the network.
            storage: An instance that implements :interface:`~kademlia.storage.IStorage`
        """
        self.ksize = ksize
        self.alpha = alpha
        self.log = Logger(system=self)
        self.storage = storage or ForgetfulStorage()
        self.node = Node(id or digest(random.getrandbits(255)))
        self.protocol = KademliaProtocol(self.node, self.storage, ksize)
        self.refreshLoop = LoopingCall(self.refreshTable).start(3600)

    def listen(self, port):
        """
        Start listening on the given port.

        This is the same as calling::

            reactor.listenUDP(port, server.protocol)
        """
        self.port = port
        return reactor.listenUDP(port, self.protocol)

    def refreshTable(self):
        """
        Refresh buckets that haven't had any lookups in the last hour
        (per section 2.3 of the paper).
        """
        ds = []
        for id in self.protocol.getRefreshIDs():
            node = Node(id)
            nearest = self.protocol.router.findNeighbors(node, self.alpha)
            spider = NodeSpiderCrawl(self.protocol, node, nearest)
            ds.append(spider.find())

        def republishKeys(_):
            ds = []
            # Republish keys older than one hour
            for key, value, timestamp in self.storage.iteritemsOlderThan(3600):
                ds.append(self.set(key, value, timestamp))
            return defer.gatherResults(ds)

        return defer.gatherResults(ds).addCallback(republishKeys)

    def bootstrappableNeighbors(self):
        """
        Get a :class:`list` of (ip, port) :class:`tuple` pairs suitable for use as an argument
        to the bootstrap method.

        The server should have been bootstrapped
        already - this is just a utility for getting some neighbors and then
        storing them if this server is going down for a while.  When it comes
        back up, the list of nodes can be used to bootstrap.
        """
        neighbors = self.protocol.router.findNeighbors(self.node)
        return [ tuple(n)[-2:] for n in neighbors ]

    def bootstrap(self, addrs):
        if self.port:
            addrs.append(("127.0.0.1", self.port))
        """
        Bootstrap the server by connecting to other known nodes in the network.

        Args:
            addrs: A `list` of (ip, port) `tuple` pairs.  Note that only IP addresses
                   are acceptable - hostnames will cause an error.
        """
        # if the transport hasn't been initialized yet, wait a second
        if self.protocol.transport is None:
            return task.deferLater(reactor, 1, self.bootstrap, addrs)

        def initTable(results):
            nodes = []
            for addr, result in results.items():
                if result[0]:
                    nodes.append(Node(result[1], addr[0], addr[1]))
            spider = NodeSpiderCrawl(self.protocol, self.node, nodes, self.ksize, self.alpha)
            return spider.find()

        ds = {}
        for addr in addrs:
            ds[addr] = self.protocol.ping(addr, self.node.id)
        return deferredDict(ds).addCallback(initTable)

    def inetVisibleIP(self):
        """
        Get the internet visible IP's of this node as other nodes see it.

        Returns:
            A `list` of IP's.  If no one can be contacted, then the `list` will be empty.
        """
        def handle(results):
            ips = [ (result[1][0],result[1][1]) for result in results if result[0] ]
            self.log.debug("other nodes think our ip is %s" % str(ips))
            return ips

        ds = []
        for neighbor in self.bootstrappableNeighbors():
            ds.append(self.protocol.stun(neighbor))
        return defer.gatherResults(ds).addCallback(handle)

    def get(self, key):
        """
        Get a key if the network has it.

        Returns:
            :class:`None` if not found, the value otherwise.
        """
        self.log.debug("Finding value at %s" % key)
        node = Node(digest(key))
        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to get key %s" % key)
            return defer.succeed(None)
        spider = ValueSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find()

    def _setWithTimestamp(self, existingValue, key, value, requestedTimeStamp, encryptionKey):
        """
        Sends the command to store the key/value pair on all required nodes.
        :param existingValue: The current (value,timestamp) associated with the key, if one exists.
        :param key: The key to store the value under.
        :param value: The value to store.
        :param requestedTimeStamp: An explicit timestamp if desired, if None the existing timestamp will be
        incremented by one.
        """
        if requestedTimeStamp is None:
            if existingValue:
                existingTimestamp = decodeTimestamp(value[1], encryptionKey)
                if not existingTimestamp:
                    return defer.succeed(False)
                timestamp = str(existingTimestamp + random.randint(1,100))
                #timestamp = existingValue[1] + 1
            else:
                timestamp = random.randint(0, 1000)

            self.log.debug("setting '%s' = '%s' on network with automatic timestamp '%s'" % (key, value, timestamp))
        else:
            timestamp = requestedTimeStamp
            self.log.debug("setting '%s' = '%s' on network with explicit timestamp '%s'" % (key, value, timestamp))

        dkey = digest(key)

        def store(nodes):
            self.log.info("setting '%s' on %s" % (key, map(str, nodes)))
            ds = [self.protocol.callStore(n, dkey, (value, encodeTimestamp(str(timestamp), encryptionKey), encryptionKey)) for n in nodes]
            return defer.DeferredList(ds).addCallback(self._anyRespondSuccess)

        node = Node(dkey)
        nearest = self.protocol.router.findNeighbors(node)
        self.log.debug("Found %s neighbours to store values at" % str(nearest))
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to set key %s" % key)
            return defer.succeed(False)
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find().addCallback(store)

    def set_contact_info(self, user_id, contact_info_list, contact_info_encryption_key, sequence_encryption_key):
        current_time = datetime.datetime.utcnow()
        self.log.debug("Current time is : %s" % current_time.strftime("%Y%m%d%M"))
        current_time = current_time - datetime.timedelta(minutes=current_time.minute % 5, seconds=current_time.second,
                                                         microseconds=current_time.microsecond)
        self.log.debug("Rounted time is : %s" % current_time.strftime("%Y%m%d%M"))

        key = user_id + current_time.strftime("%Y%m%d%M")
        contact_info_list = pickle.dumps(contact_info_list)
        self.log.debug("Pickled: %s" % str(contact_info_list))
        return self.set(key, encrypt(contact_info_encryption_key, contact_info_list), sequence_encryption_key)

    def get_contact_info(self, user_id, contact_info_encryption_key):
        currentTime = datetime.datetime.utcnow()
        self.log.debug("Current time is : %s" % currentTime.strftime("%Y%m%d%M"))
        currentTime = currentTime - datetime.timedelta(minutes=currentTime.minute % 5, seconds=currentTime.second,
                                                         microseconds=currentTime.microsecond)
        self.log.debug("Rounted time is : %s" % currentTime.strftime("%Y%m%d%M"))

        def unpackResult(result=None):
            if not result:
                return None
            self.log.debug("Unpacking %s" % str(result))
            try:
                output = pickle.loads(decrypt(contact_info_encryption_key, result[0]))
                self.log.debug("unpack output: %s" % str(output))
                return output
            except DecryptionException:
                self.log.debug("Failed to decrypt info")
                return None

        def bundleResults(resultList):
            contact_list = []
            for result in resultList:
                if type(result) is list:
                    for contact in (y for y in result if y not in contact_list):
                        contact_list.append(contact)
                else:
                    if result:
                        contact_list.append(result)

            return contact_list

        oldTime = currentTime - datetime.timedelta(minutes=-5)
        futureTime = currentTime - datetime.timedelta(minutes=5)
        oldTimeDef = self.get(user_id + oldTime.strftime("%Y%m%d%M")).addCallback(unpackResult)
        currentTimeDef = self.get(user_id + currentTime.strftime("%Y%m%d%M")).addCallback(unpackResult)
        futureTimeDef = self.get(user_id + futureTime.strftime("%Y%m%d%M")).addCallback(unpackResult)

        results = defer.gatherResults([oldTimeDef, currentTimeDef, futureTimeDef], consumeErrors=False)
        self.log.debug("Gathered %s" % results)
        return results.addCallback(bundleResults)

    def set(self, key, value, encryption_key, timestamp=None):
        """
        Set the given key to the given value in the network. A timestamp will be automatically generated if one is not
        supplied. Values will only be accepted by the hash table if their timestamps are larger than the existing values.
        :param key: The key to store the value under.
        :param value: The value to store.
        :param timestamp: Optional explicit timestamp, use None to auto set timestamp.
        :return: True if the value was successfully updated in the table.
        """
        if timestamp is None:
            self.log.debug("Checking for existing timestamp of '%s' on network before setting '%s'" % (value, key))
            return self.get(key).addCallback(self._setWithTimestamp, key=key, value=value, requestedTimeStamp=None, encryptionKey=encryption_key)
        else:
            self.log.debug("Preparing to set '%s' = '%s' with explicit timestamp '%s'" % (str(key), str(value), str(timestamp)))
            return self._setWithTimestamp(existingValue=None, key=key, value=value, requestedTimeStamp=timestamp, encryptionKey=encryption_key)

    def _anyRespondSuccess(self, responses):
        """
        Given the result of a DeferredList of calls to peers, ensure that at least
        one of them was contacted and responded with a Truthy result.
        """
        for deferSuccess, result in responses:
            peerReached, peerResponse = result
            if deferSuccess and peerReached and peerResponse:
                return True
        return False

    def saveState(self, fname):
        """
        Save the state of this node (the alpha/ksize/id/immediate neighbors)
        to a cache file with the given fname.
        """
        data = { 'ksize': self.ksize,
                 'alpha': self.alpha,
                 'id': self.node.id,
                 'neighbors': self.bootstrappableNeighbors() }
        if len(data['neighbors']) == 0:
            self.log.warning("No known neighbors, so not writing to cache.")
            return
        with open(fname, 'w') as f:
            pickle.dump(data, f)

    @classmethod
    def loadState(self, fname):
        """
        Load the state of this node (the alpha/ksize/id/immediate neighbors)
        from a cache file with the given fname.
        """
        with open(fname, 'r') as f:
            data = pickle.load(f)
        s = Server(data['ksize'], data['alpha'], data['id'])
        if len(data['neighbors']) > 0:
            s.bootstrap(data['neighbors'])
        return s

    def saveStateRegularly(self, fname, frequency=600):
        """
        Save the state of node with a given regularity to the given
        filename.

        Args:
            fname: File name to save retularly to
            frequencey: Frequency in seconds that the state should be saved.
                        By default, 10 minutes.
        """
        loop = LoopingCall(self.saveState, fname)
        loop.start(frequency)
        return loop
