Installation
==================

The easiest (and best) way to install kademlia is through `pip <http://www.pip-installer.org/>`_::

  $ pip install kademlia
      

Usage
=====
Assuming you want to connect to an existing network (run the `Stand-alone Server`_ example below if you don't have a network):

.. literalinclude:: ../examples/example.py

Check out the examples folder for other examples.


Stand-alone Server
==================

If all you want to do is run a local server, just start the example server::

  $ twistd -noy examples/server.tac


Running Tests
=============

To run tests::

  $ trial kademlia


Fidelity to Original Paper
==========================
The current implementation should be an accurate implementation of all aspects of the paper save one - in Section 2.3 there is the requirement that the original publisher of a key/value republish it every 24 hours.  This library does not do this (though you can easily do this manually).


.. _Twisted: https://twistedmatrix.com
