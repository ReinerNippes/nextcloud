Nextcloud 13
=========

Ansible Playbook to install

* Nextcloud 13
* nginx
* PHP 7.2
* MariaDB 10
* redis

In less than 20 minutes.

Most of Ubuntu settings are recommentations from C. Rieger
Visit his page for all details: https://www.c-rieger.de/nextcloud-13-installation-guide

Warning: Your existing nginx setup will be over written. Up to now I tested this only on new AWS EC2 Ubuntu and CentOS machines.

This playbook is yet not fully idempotent and will fail during the inital setup of Nextcloud when you run it twice. Will be fixed in a future release.

Requirements
------------

Ubuntu 16.04 or CentOS 7

Not yet tested with other versions and flavours of Linux.

Install
-------
```
# clone this repo
git clone https://github.com/ReinerNippes/nextcloud13

# change to nextcloud directory
cd nextcloud13

# install ansible and python-mysql
sh ./install-ubuntu.sh 
or
sh ./install-centos7.sh

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
cert_email = nc@example.org

# receive a certificate from from staging
# uncomment if you want to use letsencrypt staging environment
# cert_stage = '--staging'

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

# Nextcloud mail setup
nc_configure_mail = true
nc_mail_from         =
nc_mail_smtpmode     = smtp
nc_mail_smtpauthtype = LOGIN
nc_mail_domain       =
nc_mail_smtpname     =
nc_mail_smtpsecure   = tls
nc_mail_smtpauth     = 1
nc_mail_smtphost     =
nc_mail_smtpport     = 587
nc_mail_smtpname     =
nc_mail_smtppwd      =

#Allways get the latest version of Nextcloud
next_tgz   = https://download.nextcloud.com/server/releases/latest.tar.bz2

```

