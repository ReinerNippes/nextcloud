FROM onlyoffice/documentserver

COPY run-document-server.sh /app/onlyoffice/run-document-server.sh

EXPOSE 80 443

VOLUME /var/log/onlyoffice /var/lib/onlyoffice /var/www/onlyoffice/Data /var/lib/postgresql /usr/share/fonts/truetype/custom

ENTRYPOINT /app/onlyoffice/run-document-server.sh
