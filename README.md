# encryptedp2p

README

PROJECT DESCRIPTION

The goal of our project is to build a decentralized peer to peer chat system. This means a system which does not rely on any single server in order to work. Our focus for the first phase of this project is to use a distributed hash table system to keep track of live notes across the network. The hash table will allow network nodes (eventually chat system users) to find each other on the network and setup a direct connection.



-Code Structure-

Originally we had though to build our own distributed hash table, but that was apparently 'insane' or something, so we decided to use an existing implementation. All of out code is based off of the kademlia library. However, we decided to modify it a bit in an attempt to fix a potential table poisioning issue (more on this later). We added a timestamp and logical clock features to the the table entries. The majority of our code is for ensuring that the library is able to run correctly, and to prevent failure of the system.

-Failure Cases-

How do we handle failure cases? We don't, the kademlia library uses black magic to ensure success. Also, it does //TODO, but mostly the black magic.

for example, in the 2PC project, how are failures reflected to clients via the RPC interface that the coordinator exposes, if at all the test cases you explored, and why you picked those, along with test cases you would do if you had more time.

----------------------------------------------------------------------------------------------------------------------------

RUN INSTRUCTIONS

-Setup-

Ensure Python is installed. Version 2.7 works if 3.4 does not

Install python -dev library. This can be done on linux using 'sudo apt-get install python-dev -y'

Install Twisted. do this using 'sudo pip install twisted'

Run this because reasons 'sudo pip install rpcudp'

Copy our code to a run directory


-Run-

run 'python client.py'

run 'python server.py -p 5050'

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



