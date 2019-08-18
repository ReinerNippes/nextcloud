Nextcloud (Latest)
=========

Ansible Playbook to install

* Nextcloud (Latest) - https://nextcloud.com/
* nginx 1.17 - <https://nginx.org/>
* PHP 7.x - <http://www.php.net/>
* MariaDB 10 - <https://mariadb.org/> or PostgreSQL 10 <https://www.postgresql.org/>
* redis - <https://redis.io/>
* restic backup - <https://restic.readthedocs.io>
* Nextcloud Talk
* Collabora Online <https://www.collaboraoffice.com/>
or
* Onlyoffice <https://www.onlyoffice.com>

In less than 20 minutes.

Most of the settings are recommentations from C. Rieger

Visit his page for all details: <https://www.c-rieger.de/>

Warning: Your existing nginx/php/mariadb setup will be over written. Up to now I tested this only on newly installed AWS EC2 Ubuntu, Dedian and CentOS machines. So backup of your existing configuration is a good advice.

Requirements
------------

Ubuntu 16.04 und 18.04, CentOS 7, Debian 9 und 10, Amazon Linux 2

Not yet tested with other versions and flavours of Linux.

Install
-------

```bash
# prepare your os and install ansible
curl -s https://raw.githubusercontent.com/ReinerNippes/nextcloud/master/prepare_system.sh | /bin/bash

# clone this repo
git clone https://github.com/ReinerNippes/nextcloud

# change to nextcloud directory
cd nextcloud

# edit variables
vim inventory

# run the playbook
./nextcloud.yml

# on debian use sudo
sudo ./nextcloud.yml

# if your are fine with the defaults in the inventory (e.g. db version) just provide the ssl parameter
./nextcloud.yml -e fqdn=nc.example.org -e ssl_certificate_type=letsencrypt -e 'cert_email=nc@example.org'
or
./nextcloud.yml -e fqdn=nc.example.org -e ssl_certificate_type=selfsigned
or
./nextcloud.yml -e fqdn=nc.example.org -e ssl_certificate_type=selfsigned -e nc_db_type=mysql
```

Login to your nextcloud web site <https://nc.example.org>

Users and passwords have been set according to the entries in the inventory if defined there. Otherwise the admin password will be displayed at the end of playbook. Additional you can find them in the credential_store = /etc/nextcloud

Role Variables
--------------

All variables are defined in inventory file.

```ini
# Server domain name
# Default is the fqdn of the machine
# fqdn       = nc.example.org

# selfsigned certificate as default
ssl_certificate_type  = 'selfsigned'

# Letsencrypt or selfsigned certificate
# ssl_certificate_type  = 'letsencrypt'


# Your email adresse for letsencrypt
# cert_email = nc@example.org

# receive a certificate from staging
# uncomment if you want to use letsencrypt staging environment
# cert_stage = '--staging'

#
# Nextcloud varibales

# data dir
nc_datadir           = /var/nc-data

# admin user
nc_admin             = 'admin'
nc_passwd            = ''             # leave empty to generate random password

# database settings
# nc_db_type          = 'mysql'        # (MariaDB)
# nc_db_host          = 'localhost'
nc_db_type           = 'pgsql'        # (PostgreSQL)
nc_db_host           = ''
nc_db                = 'nextcloud'
nc_db_user           = 'nextcloud'
nc_db_passwd         = ''             # leave empty to generate random password
nc_db_prefix         = 'oc_'

# Nextcloud mail setup
nc_configure_mail    = false
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

# php Version
php_version          = '7.3'

# Install turn server for Nextcloud Talk
talk_install         = false

# Allways get the latest version of Nextcloud
next_archive         = https://download.nextcloud.com/server/releases/latest.tar.bz2

# Install restic backup tool if backup_folder is not empty
# more info about restic: https://restic.readthedocs.io/en/latest/
# to use a local directory as a restic repository (not a good idea anyway)
restic_repo          = '/var/backups/nextcloud'

# use rclone to backup a cloud storage, see https://rclone.org for more details
# configure also rclone_remote in group_vars/all.yml
# restic_repo         = "rclone:backup-selfhosted:selfhosted-{{ lookup('password', '{{ credential_store }}/restic_backup_s3_bucket_uid chars=ascii_lowercase,digits length=12') }}/backup"

# crontab setings for the backup script - default daily at 3pm
restic_backup_day    = '*'
restic_backup_minute = '0'
restic_backup_hour:  = '3'

# Install Collabra Online
# more info about collabora office: https://www.collaboraoffice.com/
install_collabora     = false

# Install Online Office
# more info about onlyoffice office: https://www.onlyoffice.com
install_onlyoffice    = false

#
# defaults path of your generated credentials (e.g. database, talk, onlyoffice)
credential_store      = /etc/nextcloud
```
