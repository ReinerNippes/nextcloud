Nextcloud 13
=========

Ansible Playbook to install

* Nextcloud 13 - https://nextcloud.com/
* nginx 1.15 - https://nginx.org/
* PHP 7.2 - http://www.php.net/
* MariaDB 10 - https://mariadb.org/ or PostgreSQL 10 https://www.postgresql.org/ (only Ubuntu right now)
* redis - https://redis.io/
* restic backup - https://restic.readthedocs.io
* Collabora Online
* Nextcloud Talk

In less than 20 minutes.

Most of settings are recommentations from C. Rieger

Visit his page for all details: https://www.c-rieger.de/nextcloud-13-nginx-installation-guide-for-ubuntu-18-04-lts/

Warning: Your existing nginx/php/mariadb setup will be over written. Up to now I tested this only on new AWS EC2 Ubuntu, Dedian and CentOS machines. So backup of your existing configuration is a good advice.


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

# if you want to use the devel branch
git checkout devel

# install ansible and python-mysql
sh ./prepare_system.sh

# edit variables
vim inventory

# run playbook
ansible-playbook nextcloud.yml

```

Log into your nextcloud web site https://\<fqdn\> 

User and password have been set according to the entries in the inventory.

Role Variables
--------------
All variables are defined in inventory file.
```
# Letsencrypt or selfsigned certificate
ssl_certificate_type  = 'letsencrypt'
#ssl_certificate_type = 'selfsigned'

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
nc_db_type          = 'mysql'    # (MariaDB)
#nc_db_type           = 'pgsql'  # (PostgreSQL docker container)
nc_db         = 'nextcloud'
nc_db_host           = 'localhost'
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

# Allways get the latest version of Nextcloud
next_archive   = https://download.nextcloud.com/server/releases/latest.tar.bz2

# Install turn server for Nextcloud Talk
talk_install         = true
# Create your personal secret by issuing "openssl rand -hex 32"
talk_static_auth_secret   = 60ca3ebe2242f79f0186bb2bf97f92b3c5411da22bf70e10d84d7b4824b706d7

# restic Backup
# if backup_folder is empty restic won't be installed
# more info about restic: https://restic.readthedocs.io/en/latest/
backup_folder   = '' # e.g. /var/nc-backup

restic_password = pML83V8DgCrexv
backup_day      = *
backup_hour     = 4
backup_minute   = 0

# Install Collabora Online
install_collabora     = true

# change dhparam numbits if generating takes to long
#dhparam_numbits = 1024
```


