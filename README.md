Nextcloud (Latest)
=========

Ansible Playbook to install

* Nextcloud (Latest) - <https://nextcloud.com/>
* nginx 1.17 - <https://nginx.org/> or Apache 2.4 <https://httpd.apache.org/>
* PHP 7.x - <http://www.php.net/>
* MariaDB 10.4 - <https://mariadb.org/> or PostgreSQL 10/11 <https://www.postgresql.org/>
* redis - <https://redis.io/>
* restic backup - <https://restic.readthedocs.io>
* Nextcloud Talk
* Fulltextsearch / Elasticsearch
* Collabora Online <https://www.collaboraoffice.com/>
or
* Onlyoffice <https://www.onlyoffice.com>

In less than 20 minutes.

Most of the settings are recommentations from C. Rieger (nginx) or Daniel Hansson (apache)

Visit his page for all details: <https://www.c-rieger.de/> or <https://www.hanssonit.se/>

> **WARNING**: Your existing nginx/php/mariadb setup will be over written. Up to now I tested this only on newly installed AWS EC2 Ubuntu, Dedian, Fedora and CentOS machines. So backup of your existing configuration is a good advice.

> **WARNING**: This playbook is not compatible with older versions. Do not run this version on older installations.

> **WARNING**: This branch is work in progress. Not all combinations are tested. Some don't work yet.

Requirements
------------

Ubuntu 16.04 und 18.04, CentOS 7, Debian 9/10 und 10, Amazon Linux 2, Fedora 30

Not yet tested with other versions and flavours of Linux.

Install
-------

```bash
# prepare your os and install ansible
curl -s https://raw.githubusercontent.com/ReinerNippes/nextcloud/master/prepare_system.sh | /bin/bash

# clone this repo
git clone --branch nextcloud-reloaded https://github.com/ReinerNippes/nextcloud

# change to nextcloud directory
cd nextcloud

# edit variables
vim inventory

# run the playbook
./nextcloud.yml

# on debian use sudo
sudo ./nextcloud.yml

# if your are fine with the defaults in the inventory (e.g. db version) just provide the ssl parameter
./nextcloud.yml -e nextcloud_fqdn=nc.example.org -e nextcloud_certificate_type=acme.sh -e 'nextcloud_cert_email=nc@example.org'
or
./nextcloud.yml -e nextcloud_fqdn=nc.example.org -e nextcloud_certificate_type=selfsigned
or
./nextcloud.yml -e nextcloud_fqdn=nc.example.org -e nextcloud_certificate_type=selfsigned -e nextcloud_db_type=mysql
```

> **WARNING**: Remember to update the inventory file if you want to run the playbook later again. E.g. to update the system. If you don't the defaults in the inventory file will be apply during the second run.

Login to your nextcloud web site <https://nc.example.org>

Users and passwords have been set according to the entries in the inventory if defined there. Otherwise the admin password will be displayed at the end of playbook. Additional you can find them in the credential_store = /etc/nextcloud

Role Variables
--------------

All variables are defined in inventory file.

```ini
# Your Nextcloud Server Domain Name

# Default is the fqdn of the Machine
nextcloud_fqdn          = nextcloud.toplevel.domain

# Selfsigned Certificate are Default
# nextcloud_certificate_type  = 'selfsigned'

# Letsencrypt Certificate provided with acme.sh (https://github.com/Neilpang/acme.sh)
nextcloud_certificate_type  = 'acme.sh'

# Your email Addresse for Letsencrypt
# nextcloud_cert_email = nc@example.org

#
# Nextcloud varibales

# Nextcloud Webserver Ports
nextcloud_web_port          = 80
nextcloud_ssl_port          = 443

# Nextcloud Web Root
nextcloud_www_dir           = /var/www/nextcloud

# Nextcloud Data Dir
nextcloud_data_dir          = /var/nc-data

# Nextcloud Admin User
# Leave Password Empty to generate secure, random one
nextcloud_admin             = 'admin'
nextcloud_passwd            = ''

# Nextcloud Database Settings
# Leave Password Empty to generate secure, random one
#nextcloud_db_type           = 'mysql'        # (MariaDB)
nextcloud_db_type           = 'pgsql'        # (PostgreSQL)
nextcloud_db_host           = 'localhost'
nextcloud_db                = 'nextcloud'
nextcloud_db_user           = 'nextcloud'
nextcloud_db_passwd         = ''
nextcloud_db_prefix         = 'oc_'

# Nextcloud Mail Setup
nextcloud_configure_mail    = false
nextcloud_mail_from         =
nextcloud_mail_smtpmode     = smtp
nextcloud_mail_smtpauthtype = LOGIN
nextcloud_mail_domain       =
nextcloud_mail_smtpname     =
nextcloud_mail_smtpsecure   = tls
nextcloud_mail_smtpauth     = 1
nextcloud_mail_smtphost     =
nextcloud_mail_smtpport     = 587
nextcloud_mail_smtpname     =
nextcloud_mail_smtppwd      =

# Allways get the latest version of Nextcloud
nextcloud_archive           = https://download.nextcloud.com/server/releases/latest.tar.bz2

# webserver type nginx or apache
nextcloud_webserver_type    = nginx

# php Version
php_version                 = '7.4'
# optional php packages see: roles/php/var/main.yml
php_install_optional_packages = false

# Install turn server for Nextcloud Talk
talk_install                = false

# Install restic backup tool if backup_folder is not empty
# more info about restic: https://restic.readthedocs.io/en/latest/
# to use a local directory as a restic repository (not a good idea anyway)
restic_repo                 = '/var/backups/nextcloud'

# use rclone to backup a cloud storage, see https://rclone.org for more details
# configure also rclone_remote in group_vars/all.yml
# restic_repo         = "rclone:backup-selfhosted:selfhosted-{{ lookup('password', '{{ credential_store }}/restic_backup_s3_bucket_uid chars=ascii_lowercase,digits length=12') }}/backup"

# crontab setings for the backup script - default daily at 3pm
restic_backup_day           = '*'
restic_backup_minute        = '0'
restic_backup_hour:         = '3'

# Install Collabra Online
# more info about collabora office: https://www.collaboraoffice.com/
install_collabora           = false

# Install Online Office
# more info about onlyoffice office: https://www.onlyoffice.com
install_onlyoffice          = false
onlyoffice_ssl_port         = 8443

# Install fulltextsearch
install_fulltextsearch      = false
```
