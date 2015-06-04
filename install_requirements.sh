#! /bin/bash

if [ $1 -eq "server"  ];then
    echo "Installing requirements for server"
    source virtualenv/kademlia/bin/activate && pip install -r requirements/server.txt
elif [ $1 -eq "client"  ] then
    echo "Installing requirements for client"
    source virtualenv/kademlia/bin/activate && pip install -r requirements/client.txt
else then
    echo "Invalid input $1. Please choose client or server"
    exit(1)
fi


