# encryptedp2p

README

PROJECT DESCRIPTION

The goal of our project is to build a decentralized peer to peer chat system. This means a system which does not rely on any single server in order to work. Our focus for the first phase of this project is to use a distributed hash table system to keep track of live notes across the network. The hash table will allow network nodes (eventually chat system users) to find each other on the network and setup a direct connection.

The second phase of our project involved us hooking up the hash table to a front end client, sending messages, and  building some security into the table itself to avoid malicious parties from poisoning the table.


-Code Structure-

Originally we had though to build our own distributed hash table, but that was apparently 'insane' or something, so we decided to use an existing implementation. All of our code is based off of the Kademlia library (a link has been provided at the bottom of the page). However, we decided to modify it a bit in an attempt to fix a potential table poisoning issue (more on this later). We added a logical timestamp to the the table entries. The majority of our code is for ensuring that the library is able to run correctly, and to prevent failure of the system.

-Modifications to the existing Kademlia library

The Kademlia distributed hash table relies on fairly stable nodes. For a chat system it is quite likely that nodes (chat clients) will be starting and stopping quite often, and the network connecting them may be unstable. As an example a user running the client on a laptop may move away from a Wi-Fi hotspot which disconnects them from the network. When a node becomes disconnected from the network it can no longer update values to the hash table or be updated. Once it reconnects it may be storing stale values, or have new values which need to be pushed into the table. We added a timestamp to every value stored in the hash table so that the newest values are used if there is any conflict. A single new value will over-ride a large number of old values when the table is queried.

The timestamps start at zero and are incremented each time the value is updated. To do this the library will check the current timestamp of the key in the table by accessing the hash table normally, if there is no value stored it will start from zero, otherwise it will increment by one. This will likely decrease the performance of the set() method but any delay here is inherent in the nature of the distributed hash table and will affect the entire program. If the delay is an issue it will have to be solved for the entire program.

Due to the rapidly changing nature of the network clients must push their data onto the table fairly regularly, currently we imagine this should happen roughly every five minutes. This puts an upper limit on the time a user will have access to bad data.

-Failure Cases-

How do we handle failure cases? We don't for the most part, the Kademlia library contains solutions to a lot of the problems associated with distributed hash tables (though it likely uses black magic to ensure success). The main problem we focused on was preventing hash tables from being poisoned by outdated IP addresses. Adding the timestamp to the hash table was our attempt at solving this, as was described above.

There are two main tests that we performed on our system.
First we needed to test what happened when a node disconnects? Nodes could go down at any time for any reason, and our system needs to recover. The test we performed was to get our system running, then disconnect a node, or several nodes, and observe the results.

Second, we tested what happened when old nodes (that had disconnected before) were re-added to the network. Specifically  what happens if their IP address changes while they are offline.

-Future Tests-

In future, we would like to experiment with different network connectivity speeds, limited bandwidths, and forced partial connectivity cases across the connected nodes. Ensuring our system could handle these scenarios would be preferred, but setting up the testing system for achieving these reliable was outside of this project's scope.

Another thing we would like to test is the systems security. With the current system, it is entirely possible to overwhelm the system with false timestamps, thereby poisoning the entries. Testing this will help us devise a potential solution to our modified code.

----------------------------------------------------------------------------------------------------------------------------

RUN INSTRUCTIONS

-Setup-

Ensure Python is installed. Version 2.7 works if 3.4 does not
Note: ensure that apt-get is up to date (run 'apt-get update') (if using ubuntu)

To Run a dedicated server:

'sudo apt-get install python-pip python-dev -y'

'sudo pip install twisted rpcudp simple-crypt'

To run the a client node, do all the steps above and:

'sudo apt-get install python-tk'


Copy our code to a run directory:
Specifically, client-node.py, dedicated-server.py, the config.py (optional), and the kademelia folder from our github repository.

Make sure to maintain the directory structure. The cilent-node and dedicated-server should be in the same directory as the kademlia server.

You should also have two text files in your run directory. An identity.txt file that contains your public key as well as your username, space separated.
Plus a contacts.txt file containing the public keys and usernames of your contacts/friends, again space separated.

Both files should take the form:
<key> <name>

Optionally, you can have a bootstrap.txt file with space separated IP/port pairs that will supply the client with a list
of bootstrappable nodes to check.

-Run-

Run 'python dedicated-server.py -p \<port\>' on at least one network node.
This starts a server meant to get the initial system running. After that, the client nodes should be able to connect to each other.

To run your chat client. Run the client-node.py file.

python client-node.py

There are a number of options you can use to run the client node. Those annotated with a * will override the value set in your config.txt
file:

- -p \<the port you are running your kademlia server on\>*
- -I \<A bootstrappable IP. Needs to be paried with a -P\>*
- -P \<A bootstarppable port for the IP above.\>*
- -l \<A log file to save to (defaults to stdout)\>*
- -N \<An option to run the client without a GUI (currently not functional WITHOUT a GUI)\>
- -r \<Refresh your contacts list every 10 seconds (otherwise has to be done manually)\>

----------------------------------------------------------------------------------------------------------------------------
-The Future-

For the next part of the project. We plan to flesh our modifications to Kademlia, build more robust test cases, test NAT traversal etc.


The next steps for kademlia involve adding secure communications on top of the existing backend. Currently all information is stored as plain text which is not useful for a secure chat application. Any malicious client can currently overwrite key/value pairs through two ways. If the client knows a user's key they can set a new value for that user through normal means. If a malicious client does not have any users' keys they can check the keys stored on their local node and use those keys (although this is not useful for targeting a specific user it can still disrupt the system). There needs to be some way to stop these clients from pushing values with a larger sequence number to redirect traffic. Likely the easiest way to secure the tables is by using a difficult to determine key and encrypting the values. A malicious user will be able to set values in the table at random, but not target a specific user. The desired recipient will need both the key, and a way to decode the value. Using a public encryption key for both the table key and decrypting the value would be easy but it means that any time a node stores a value the key can be compromised.

Stopping broad attacks against the table is much harder however. There needs to be some way to detect and stop malicious clients which are trying to push values onto the table for keys which belong to other clients. This is difficult since ideally the public key of a user should never be shared to the hash table, only directly between two users who wish to chat.

The hash table should also handle time stamped values better. If a node is separated from the network and it gets a newer value it should repopulate the entire hash table with this new value as soon as it is able, but currently it will just hold the its value until the client overwrites the table. Since the library will now always select the value with the largest timestamp this isn't a critical issue but it significantly reduces the fault tolerance of the system until the client resets the value. This can become a much more significant problem some clients are unable to talk to other clients and the values are not propagated through the entire table.

The ideal level of replication inside Kademlia still needs to be determined. This should be based on how likely a node is to go down (how long does an average user keep a chat application up), how often do we want to republish values to the table (every 5 - 10 minutes maybe), and what level of reliability is desired. This feels like it should be independent of the number of users but doing a quick statistical analysis might be interesting.

-Current Progress on Kademlia Improvements-

For part two of the project a place holder security implementation was added. It provides no true security but mirrors what we belive to be a workable design for table security. Every value which is entered into the table has a sequence number/timestamp assigned to it as discussed above. Encryption is used to protect these keys from malicious users.

Each user generates two key pairs when they first joining the system. The first private/public key pair is used to secure their contact information and is not made widely available, only desired contacts should have access to the public key. Without this key it should not be possible to decrypt a user's IP/port.

The second key pair is used to secure the sequence numbers of any values a user places into the table. When a user creates a new value in the table they add the value itself, an encrypted version of the sequence number, the key required to decrypt the sequence number, and a TTL counter which is discussed below. Currently a simple single key cypher is used which does not provide any meaningful security since any user may encrypt new sequence numbers using it. In the future this will be replaced with a two key system such as RSA. Any node receiving a store command will only store a value if the new sequence number's key matches the old sequence number, and the new sequence number is larger.

This system will only protect values which are already in the table, a malicious user could wait for a legitimate user to be offline and replace their contact information with a different key. To make this much more difficult the location contact information is stored in the table changes over time. Every five minutes the contact information moves to a new location. The key used is deterministic, basically the user's ID followed by the current time rounded to the nearest five minutes, but the hash generated from these new keys is random. For a malicious user to hijack a legitimate users traffic for more than a few minutes they must determine a sequence of hash values and squat on all of them.

This still does not stop a user from flooding the table with large numbers of garbage values but it does make it much harder to target specific users. Some sort of detection system might ignore users which spam too many store requests.

Since the contact information keys are constantly changing old keys do not need to be kept, and in fact should be removed to decrease the chance of collisions. Kademlia is meant as a semi-permanent data store where values will persist for as long as they are accessed on a regular basis. This doesn't make sense for our system so each value has a very tight limit of 10 minutes for any given key/value pair. Unlike Kademlia which keeps count locally only this TTL is transferred across nodes during replication. Every minute each node will decrement the TTL counters and remove any which reach zero. A user is responsible for updating their contact information on a regular basis.

-Other Work in Progress-

We have a GUI to work with our chat client, and it does function to some extent. However there is still work to be done:
- In order to deal with NAT traversal, we will poll the other nodes for our public ip/port. However, different nodes can see different IP/port pairs. We need to add in functionality to determine which IP/port pair will work when trying to communicate with another client.
- The encryption scheme we use at present is very slow, and it halts the rest of the application. There are likely ways we can improve performance.
- Currently chats are all sent and received in the same window. So it is hard to tell each conversation apart. An update to the GUI would be to separate each conversation.
- When a client disconnects, they don't tell the swarm they have left. Their value is still in the DHT and they are still considered to be "online", but chat will not connect. Upon shutting down, the value should be removed from the DHT, therefore telling the world the node is offline.

----------------------------------------------------------------------------------------------------------------------------
Videos!
This is a proof of concept video.
https://youtu.be/NVkZQG3EdkI
You didn't see the stacktrace...
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
