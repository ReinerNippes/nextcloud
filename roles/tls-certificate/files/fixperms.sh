#!/bin/bash

set -euo pipefail

CERT_GROUP="${CERT_GROUP:-ssl-cert}"

chmod 640 "$CERT_KEY_PATH"

if getent group "$CERT_GROUP" >/dev/null 2>&1; then
	chown "root:${CERT_GROUP}" "$CERT_KEY_PATH"
else
	chown root:root "$CERT_KEY_PATH"
fi

chmod 644 "$CERT_PATH" "$CERT_FULLCHAIN_PATH"

# Apply optional ACLs only if tools and target users already exist.
if command -v setfacl >/dev/null 2>&1; then
	if id coturn >/dev/null 2>&1; then
		setfacl -m u:coturn:r "$CERT_KEY_PATH" "$CERT_PATH" "$CERT_FULLCHAIN_PATH" || true
	fi

	if id turnserver >/dev/null 2>&1; then
		setfacl -m u:turnserver:r "$CERT_KEY_PATH" "$CERT_PATH" "$CERT_FULLCHAIN_PATH" || true
	fi
fi
