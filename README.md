Nextcloud 13
=========

Ansible Playbook to install

* Nextcloud 13
* nginx
* PHP 7.2
* MariaDB
* redis

In less than 20 minutes.

All settings are recommentations from C. Rieger
Visit his page for all details: https://www.c-rieger.de/nextcloud-13-installation-guide

Warning: Your existing nginx setup will be over written. Up to now I tested this only on new AWS EC2 Ubuntu machines.

This playbook is yet not fully idempotent and will fail during the inital setup of Nextcloud when you run it twice. Will be fixed in a future release.

Requirements
------------

Ubuntu 16.04 
Not yet tested with other versions and flavours of Linux.

Install
-------
```
# clone this repo
git clone https://github.com/ReinerNippes/nextcloud13.git

# change to nextcloud directory
cd nextcloud

# install ansible and python-mysql
sh ./install.sh

# edit variables
vim inventory

# run playbook
ansible-playbook nextcloud.yml
```

Log into your nextcloud web site

Role Variables
--------------
All variables are defined in inventory.
```
# 
# Your domain name to get a letsencrypt certificate
fqdn       = nc.example.org

# Your email adresse for letsencrypt
cert_email = nc@example.com

# Your dns resolver (nginx reverse ip lookup)
# e.g. your fritz.box ; default ist google dns server 8.8.8.8
nginx_resolver = '8.8.8.8'

# Nextcloud varibales

# data dir
nc_datadir = /var/nc-data

# admin user
nc_admin   = 'admin'
nc_passwd  = 'tOpSecrET2018'

# database
nc_db         = 'nextcloud'
nc_db_user    = 'nextcloud'
nc_db_passwd  = 'next12345'
nc_db_prefix  = 'oc_'

#Allways get the latest version of Nextcloud
next_tgz   = https://download.nextcloud.com/server/releases/latest.tar.bz2

```


License
-------

MIT

