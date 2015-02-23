# encryptedp2p

README

PROJECT DESCRIPTION

The goal of our project is to build a decentralized peer to peer chat system. This means a system which does not rely on any single server in order to work. Our focus for the first phase of this project is to use a distributed hash table system to keep track of live notes across the network. The hash table will allow network nodes (eventually chat system users) to find each other on the network and setup a direct connection.



-Code Structure-

Originally we had though to build our own distributed hash table, but that was apparently 'insane' or something, so we decided to use an existing implementation. All of out code is based off of the kademlia library. However, we decided to modify it a bit in an attempt to fix a potential table poisioning issue (more on this later). We added a timestamp and logical clock features to the the table entries. The majority of our code is for ensuring that the library is able to run correctly, and to prevent failure of the system.

-Modifications to the existing kademlia library

The kademlia distributed hash table relies on fairly stable nodes. For a chat system it is quite likely that nodes (chat clients) will be starting and stopping quite often, and the network connecting them may be unstable. As an example a user running the client on a laptop may move away from a wi-fi hotspot which disconnects them from the network. When a node becomes disconnected from the network it can no longer update values to the hash table or be updated. Once it reconnects it may be storing stale values, or have new values which need to be pushed into the table. We added a timestamp to every value stored in the hash table so that the newest values are used if there is any conflict. A single new value will over-ride a large number of old values when the table is queried.

The timestamps start at zero and are incremented each time the value is updated. To do this the library will check the current timestamp of the key in the table by accessing the hash table normally, if there is no value stored it will start from zero, otherwise it will increment by one. This will likely decrease the performance of the set() method but any delay here is inherent in the nature of the distributed hash table and will affect the entire program. If the delay is an issue it will have to be solved for the entire program.

Due to the rapidly chaning nature of the network clients must push their data onto the table fairly regularly, currently we imagine this should happen roughly every five minutes. This puts an upper limit on the time a user will have access to bad data.

-Failure Cases-

How do we handle failure cases? We don't, the kademlia library uses black magic to ensure success. Also, it does //TODO, but mostly the black magic.

for example, in the 2PC project, how are failures reflected to clients via the RPC interface that the coordinator exposes, if at all the test cases you explored, and why you picked those, along with test cases you would do if you had more time.

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
Specifically, client.py, server.py, and the kademelia folder from our github repository.

-Run-

run 'python client.py' on each network node.

run 'python server.py -p 5050' on at least one network node.

----------------------------------------------------------------------------------------------------------------------------
-The Future-

For the next part of the project. We plan to flesh our our modifications to Kademlia, build more robust test cases, test NAT traversal etc.


After solidifying Kademlia, we will start building our P2P client on top of it. 



A major stretch goal would be to build a Python GUI to create a "usable" client.
Possible libraries we can use for an event given GUI would be Tkinter http://www.openbookproject.net/py4fun/gui/tkPhone.html
or  wxPython
http://www.openbookproject.net/py4fun/gui/wxPhone.html



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



