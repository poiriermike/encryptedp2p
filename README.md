# encryptedp2p

README

PROJECT DESCRIPTION

The goal of our project is to build a decentralized peer to peer chat system. This means a system which does not rely on any single server in order to work. Our focus for the first phase of this project is to use a distributed hash table system to keep track of live notes across the network. The hash table will allow network nodes (eventually chat system users) to find each other on the network and setup a direct connection.



-Code Structure-

Originally we had though to build our own distributed hash table, but that was apparently 'insane' or something, so we decided to use an existing implementation. All of our code is based off of the Kademlia library. However, we decided to modify it a bit in an attempt to fix a potential table poisioning issue (more on this later). We added a logical timestamp to the the table entries. The majority of our code is for ensuring that the library is able to run correctly, and to prevent failure of the system.

-Modifications to the existing Kademlia library

The Kademlia distributed hash table relies on fairly stable nodes. For a chat system it is quite likely that nodes (chat clients) will be starting and stopping quite often, and the network connecting them may be unstable. As an example a user running the client on a laptop may move away from a wi-fi hotspot which disconnects them from the network. When a node becomes disconnected from the network it can no longer update values to the hash table or be updated. Once it reconnects it may be storing stale values, or have new values which need to be pushed into the table. We added a timestamp to every value stored in the hash table so that the newest values are used if there is any conflict. A single new value will over-ride a large number of old values when the table is queried.

The timestamps start at zero and are incremented each time the value is updated. To do this the library will check the current timestamp of the key in the table by accessing the hash table normally, if there is no value stored it will start from zero, otherwise it will increment by one. This will likely decrease the performance of the set() method but any delay here is inherent in the nature of the distributed hash table and will affect the entire program. If the delay is an issue it will have to be solved for the entire program.

Due to the rapidly chaning nature of the network clients must push their data onto the table fairly regularly, currently we imagine this should happen roughly every five minutes. This puts an upper limit on the time a user will have access to bad data.

-Failure Cases-

How do we handle failure cases? We don't for the most part, the Kademlia library contains solutions to a lot of the problems associated with distributed hash tables (though it likely uses black magic to ensure success). The main problem we focused on was preventing hash tables from being poisoned by outdated IP addresses. Adding the timestamp to the hash table was our attempt at solving this, as was described above.

-Future Tests-

In future, we would like to experiment with different network connectivity speeds, limited bandwidths, and forced partial connectivity cases across the connected nodes. Ensuring our system could handle these senarios would be prefered, but seting up the testing system for acheiving these reliable was outside of this project's scope.

Another thing we would like to test is the systems security. With the current system, it is entirely possible to overwhelm the system with false timestamps, thereby poisoning the entries. Testing this will help us devise a potential solution to our modified code.

----------------------------------------------------------------------------------------------------------------------------

RUN INSTRUCTIONS

-Setup-
For each computer in the network do the following.
We reccoment using fabric to run all these instructions in parellel on all the nodes.

Note: ensure that apt-get is up to date (run 'apt-get update')

Ensure Python is installed. Version 2.7 works if 3.4 does not

Install python -dev library. This can be done on linux using 'sudo apt-get install python-dev -y'

Install Twisted. do this using 'sudo pip install twisted'

Run this because reasons 'sudo pip install rpcudp'

Copy our code to a run directory:
Specifically, client-node.py, dedicated-server.py, and the kademelia folder from our github repository.

-Run-

run 'python dedicated-server.py -p 5050' on at least one network node.
This starts a server meant to get the initial system running. After that, the client nodes should be able to connect to each other.

run 'python client-node.py' on each network node.

----------------------------------------------------------------------------------------------------------------------------
-The Future-

For the next part of the project. We plan to flesh our our modifications to Kademlia, build more robust test cases, test NAT traversal etc.


The next steps for kademlia involve adding secure communications on top of the existing backend. Currently all information is stored as plain text which is not useful for a secure chat application. Any malicious client can currently overwrite key/value pairs through two ways. If the client knows a user's key they can set a new value for that user through normal means. If a malicious client does not have any users' keys they can check the keys stored on their local node and use those keys (although this is not useful for targeting a specific user it can still disrupt the system). There needs to be some way to stop these clients from pushing values with a larger sequence number to redirect traffic. Likely the easiest way to secure the tables is by using a difficult to determine key and encrypting the values. A malicious user will be able to set values in the table at random, but not target a specific user. The desired recipient will need both the key, and a way to decode the value. Using a public encryption key for both the table key and decypting the value would be easy but it means that any time a node stores a value the key can be compromized. 

Stoping broad attacks against the table is much harder however. There needs to be some way to detect and stop malicious clients which are trying to push values onto the table for keys which belong to other clients. This is difficult since idealy the public key of a user should never be shared to the hash table, only directly between two users who wish to chat.

The hash table should also handle timestamped values better. If a node is seperated from the network and it gets a newer value it should repopulate the entire hash table with this new value as soon as it is able, but currently it will just hold the its value until the client overwrites the table. Since the library will now always select the value with the largest timestamp this isn't a critical issue but it significantly reduces the fault tolerance of the system until the client resets the value. This can become a much more significant problem some clients are unable to talk to other clients and the values are not propagated through the entire table.

The ideal level of replication inside Kademlia still needs to be determined. This should be based on how likely a node is to go down (how long does an average user keep a chat application up), how often do we want to republish values to the table (every 5 - 10 minutes maybe), and what level of reliability is desired. This feels like it should be independant of the number of users but doing a quick statistical analysis might be interesting.

After solidifying Kademlia, we will start building our P2P client on top of it. 


A major stretch goal would be to build a Python GUI to create a "usable" client.
Possible libraries we can use for an event given GUI would be Tkinter: http://www.openbookproject.net/py4fun/gui/tkPhone.html
or  wxPython:
http://www.openbookproject.net/py4fun/gui/wxPhone.html

Here is a comprehensive list of GUIs that could work with Twisted: http://twistedmatrix.com/documents/13.2.0/core/howto/choosing-reactor.html



----------------------------------------------------------------------------------------------------------------------------
OTHER STUFF

This is a readme file. Things will go here eventually. Muahahahaha.

Here is a list of potential software choices for a DHT as well as the popular algorithm that BitTorrent and many other P2P protocols use.

http://en.wikipedia.org/wiki/Kademlia#Implementations

https://github.com/maidsafe/MaidSafe-Routing

https://github.com/ytakano/libcage

https://github.com/bmuller/kademlia

NOTE: This Python library requires the python-dev package to run. On Ubuntu based systems you can run: sudo apt-get install python-dev -y to install it. Then follow the instructions in the Kademila docs.

https://twistedmatrix.com/trac/

http://findingscience.com/python/kademlia/dht/2014/02/14/kademlia:-a-dht-in-python.html



