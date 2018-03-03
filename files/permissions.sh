#!/bin/bash
find /var/www/ -type f -print0 | xargs -0 chmod 0640
find /var/www/ -type d -print0 | xargs -0 chmod 0750
chown -R $WEB_USER:$WEB_GROUP /var/www/
chown -R $WEB_USER:$WEB_GROUP /upload_tmp/
chown -R $WEB_USER:$WEB_GROUP $NC_DATADIR
chmod 0644 /var/www/nextcloud/.htaccess
chmod 0644 /var/www/nextcloud/.user.ini
chmod 600 /etc/letsencrypt/live/$FQDN/fullchain.pem
chmod 600 /etc/letsencrypt/live/$FQDN/privkey.pem
chmod 600 /etc/letsencrypt/live/$FQDN/chain.pem
chmod 600 /etc/letsencrypt/live/$FQDN/cert.pem
chmod 600 /etc/ssl/certs/dhparam.pem
exit 0
