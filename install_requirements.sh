#! /bin/bash

if [ $1 == "server"  ] 
then
    echo "Installing requirements for server"
    pip install -r requirements/server.txt
elif [ $1 == "client"  ] 
then
    echo "Installing requirements for client"
    pip install -r requirements/client.txt
else 
    echo "Invalid input \"$1\". Please choose client or server"
    exit 1
fi


