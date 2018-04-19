#!/bin/bash

#sudo echo "deb http://ppa.launchpad.net/ansible/ansible/ubuntu trusty main" >> /etc/apt/sources.list
sudo apt install dirmngr -y
#sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
sudo apt update -y
sudo apt install python-mysqldb python-pip python3-pip -y
sudo pip install pip -U
sudo pip install setuptools -U
sudo pip install ansible -U
