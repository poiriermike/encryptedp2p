"""
Package for interacting on the network at a high level.
"""
from _ast import expr
import random
import pickle
import re

from simplecrypt import encrypt, decrypt, DecryptionException

from twisted.internet.task import LoopingCall
from twisted.internet import defer, reactor, task

from kademlia.log import Logger
from kademlia.protocol import KademliaProtocol
from kademlia.utils import deferredDict, digest
from kademlia.storage import ForgetfulStorage
from kademlia.node import Node
from kademlia.crawling import ValueSpiderCrawl
from kademlia.crawling import NodeSpiderCrawl


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
        self.protocol = KademliaProtocol(self.node, self.storage, ksize, self)
        self.refreshLoop = LoopingCall(self.refreshTable).start(3600)

    def listen(self, port):
        """
        Start listening on the given port.

        This is the same as calling::

            reactor.listenUDP(port, server.protocol)
        """
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

    def findencryptionkey(self, encrypted_key_location):
        """
        Finds the encryption key associated with the value stored at encrypted_key_location.
        :param encrypted_key_location: The location of the object to decrypt.
        :return: The encryption key required to decrypt the object stored at key.
        """

        # TODO: Check for a signature here instead of blindly passing it back!
        return defer.maybeDeferred(self.get, str(encrypted_key_location+'encryption_key_location'), True)


    def _finish_get(self, encryption_key, node, nearest, key, self_signed):
        spider = ValueSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha, encryption_key, self)
        return spider.find()

    def get(self, key, self_signed=False):
        """
        Get a key if the network has it.

        Returns:
            :class:`None` if not found, the value otherwise.
        """
        self.log.debug("Finding what value is at (%s)" % key)
        if self_signed:
            self.log.debug("Self signed")
        node = Node(digest(key))
        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to get key %s" % key)
            return defer.succeed(None)
        encryption_key = None
        if not self_signed:
            self.log.debug("Value is not self signed, need to find the key")
            d = self.findencryptionkey(key)
            self.log.debug("done launching find encryption key")
            return d.addCallback(self._finish_get, node, nearest, key, self_signed)
        return self._finish_get(encryption_key, node, nearest, key, self_signed)

    def evaluate_timestamp(self, encrypted_timestamp, encryption_key):
        self.log.debug("Eval Timestamp! (key:%s) " % encryption_key)
        self.log.debug(type(encrypted_timestamp))
        if not encryption_key or not encrypted_timestamp:
            return None
        try:
            str_timestamp = decrypt(encryption_key,encrypted_timestamp)
        except DecryptionException:
            self.log.debug("Can't decode the timestamp!")
            str_timestamp = ""

        self.log.info("Evaluating timestamp %s" % str_timestamp)
        p = re.compile('^timestamp(\d+)$')
        match = p.match(str_timestamp)
        if match:
            self.log.info("Found %s" % match.group(1))
            return int(match.group(1))
        else:
            return None


    def _setWithTimestamp(self, existingValue, key, value, requestedTimeStamp, encryptionkey, encryption_key_location):
        """
        Sends the command to store the key/value pair on all required nodes.
        :param existingValue: The current (value,timestamp) associated with the key, if one exists.
        :param key: The key to store the value under.
        :param value: The value to store.
        :param requestedTimeStamp: An explicit timestamp if desired, if None the existing timestamp will be
        incremented by a small random amount.
        :param encryptionkey: The desired encryption key for the sequence numbers.
        """
        if requestedTimeStamp is None:
            #Automatically select the timestamp.
            if existingValue:
                #We have an existing value, just increment it.
                existing_timestamp = self.evaluate_timestamp(existingValue[1], encryptionkey)
                if existing_timestamp is None:
                    self.log.warning("Failed to decrypt the existing timestamp!")
                    return defer.succeed(False)
                timestamp = str('timestamp' + str(int(existing_timestamp + random.randint(1, 100))))
            else:
                #Start a new value
                self.log.debug("No existing value, starting new automatic timestamp!")
                timestamp = str('timestamp' + str(random.randint(0, 1000)))

            self.log.debug("setting '%s' = '%s' on network with automatic timestamp '%s'" % (key, value, timestamp))
        else:
            timestamp = str(requestedTimeStamp)
            self.log.debug("setting '%s' = '%s' on network with explicit timestamp '%s'" % (key, value, timestamp))

        timestamp = encrypt(encryptionkey, timestamp)
        self.log.debug(type(timestamp))

        dkey = digest(key)

        def store(nodes):
            self.log.info("setting '%s' on %s" % (key, map(str, nodes)))
            ds = [self.protocol.callStore(node, dkey, (value, timestamp, encryption_key_location),
                                          key == encryption_key_location) for node in nodes]
            return defer.DeferredList(ds).addCallback(self._anyRespondSuccess)

        node = Node(dkey)
        nearest = self.protocol.router.findNeighbors(node)
        if len(nearest) == 0:
            self.log.warning("There are no known neighbors to set key %s" % key)
            return defer.succeed(False)
        spider = NodeSpiderCrawl(self.protocol, node, nearest, self.ksize, self.alpha)
        return spider.find().addCallback(store)

    def set_encryption_key(self, key, encryption_key):
        """
        Sets the encryption key for a normal value stored in the table. All subsequent changes made the value
        must use this encryption key. This key is set on a first come first serve basis! (This needs to be fixed
        as this is a huge security flaw and will allow any malicious user to assume control of  a value in the table.
        :param key: They key of the value the encryption should apply to.
        :param encryption_key: The encryption key which will be used to encrypt the value stored at 'key'
        :return:
        """
        self.log.debug("Setting an encryption key for a value stored at %s" % key)
        return self.set(key+'encryption_key_location', encryption_key, None)


    def set(self, key, value, explicit_encryption_key, timestamp=None):
        """
        Set the given key to the given value in the network. A timestamp will be automatically generated if one is not
        supplied. Values will only be accepted by the hash table if their timestamps are larger than the existing values.
        :param key: The key to store the value under.
        :param value: The value to store.
        :param timestamp: Optional explicit timestamp, use None to auto set timestamp.
        :param explicit_encryption_key: Force a specific key to secure the timestamps rather than look it up.
        :return: True if the value was successfully updated in the table.
        """
        # if explicit_encryption_key is None:
        #     encryption_key = self.findencryptionkey(key)
        # else:
        #     encryption_key = explicit_encryption_key

        self.log.debug("Setting a value (%s) at location (%s) with encryption (%s)" % (str(value), str(key), str(explicit_encryption_key)))
        if explicit_encryption_key is None:
            encryption_key = value
            encryption_key_location = key
        else:
            encryption_key = explicit_encryption_key
            encryption_key_location = key+'encryption_key_location'

        if timestamp is None:
            self.log.debug("Checking for existing timestamp of '%s' on network before setting new value at '%s'" % (value, key))
            return self.get(key, explicit_encryption_key is None).\
                addCallback(self._setWithTimestamp, key=key, value=value, requestedTimeStamp=None, encryptionkey=encryption_key,
                            encryption_key_location=encryption_key_location)
        else:
            self.log.debug("Preparing to set '%s' = '%s' with explicit timestamp '%s'" % (str(key),
                                                                                          str(value), str(timestamp)))
            return self._setWithTimestamp(existingValue=None, key=key, value=value, requestedTimeStamp=timestamp,
                                          encryptionkey=encryption_key, encryption_key_location=encryption_key_location)

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
