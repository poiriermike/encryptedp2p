# encryptedp2p

README

PROJECT DESCRIPTION

a description of the following:

the structure of your code, including any major interfaces you implemented 
for example, in the 2PC project, the RPC interface your replicas expose to the coordinator

how you handle failures 

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



