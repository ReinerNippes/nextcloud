Nextcloud 13
=========

Ansible Playbook to install

* Nextcloud 13 - https://nextcloud.com/
* nginx 1.14 - https://nginx.org/
* PHP 7.2 - http://www.php.net/
* MariaDB 10 - https://mariadb.org/
* redis - https://redis.io/
* restic backup - https://restic.readthedocs.io

In less than 20 minutes.

Most of settings are recommentations from C. Rieger

Visit his page for all details: https://www.c-rieger.de/nextcloud-13-nginx-installation-guide-for-ubuntu-18-04-lts/

Warning: Your existing nginx setup will be over written. Up to now I tested this only on new AWS EC2 Ubuntu, Dedian and CentOS machines. So backup of your existing configuration is a good advice.


Requirements
------------

Ubuntu 16.04, Ubuntu 18.04, CentOS 7 or Debian 9

Not yet tested with other versions and flavours of Linux.

Install
-------
```
# clone this repo
git clone https://github.com/ReinerNippes/nextcloud13

# change to nextcloud directory
cd nextcloud13

# install ansible and python-mysql
sh ./prepare_system.sh

# edit variables
vim inventory

# run playbook
ansible-playbook nextcloud.yml

```

Login to your nextcloud web site https://\<fqdn\> 
User and password have been set according to the entries in the inventory.

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

# change dhparam numbits if generating takes to long
#dhparam_numbits = 1024

```


