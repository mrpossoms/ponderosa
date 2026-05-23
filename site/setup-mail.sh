#!/usr/bin/env bash
# setup-mail.sh — configure Postfix + OpenDKIM for ponderosafireprotection.com
# Run as root on the production server.
set -euo pipefail

DOMAIN="ponderosafireprotection.com"
FROM="reports@${DOMAIN}"
SELECTOR="mail"
KEY_DIR="/etc/opendkim/keys/${DOMAIN}"
OPENDKIM_SOCK="/run/opendkim/opendkim.sock"

# ---------------------------------------------------------------------------
# 1. Detect server's public IP
# ---------------------------------------------------------------------------
SERVER_IP=$(curl -4 -sf https://ifconfig.me || hostname -I | awk '{print $1}')
echo "Server IP: ${SERVER_IP}"

# ---------------------------------------------------------------------------
# 2. Install packages
# ---------------------------------------------------------------------------
apt-get update -q
DEBIAN_FRONTEND=noninteractive apt-get install -y postfix opendkim opendkim-tools mailutils

# ---------------------------------------------------------------------------
# 3. Configure Postfix
# ---------------------------------------------------------------------------
postconf -e "myhostname = ${DOMAIN}"
postconf -e "myorigin = ${DOMAIN}"
postconf -e "mydestination ="
postconf -e "local_transport = error: local delivery disabled"
postconf -e "inet_interfaces = loopback-only"
postconf -e "inet_protocols = ipv4"
postconf -e "sender_canonical_maps = static:${FROM}"
postconf -e "milter_default_action = accept"
postconf -e "smtpd_milters = unix:${OPENDKIM_SOCK}"
postconf -e "non_smtpd_milters = unix:${OPENDKIM_SOCK}"

# ---------------------------------------------------------------------------
# 4. Generate DKIM key (skip if key already exists)
# ---------------------------------------------------------------------------
mkdir -p "${KEY_DIR}"
if [[ ! -f "${KEY_DIR}/${SELECTOR}.private" ]]; then
    opendkim-genkey -D "${KEY_DIR}/" -s "${SELECTOR}" -d "${DOMAIN}"
    chown -R opendkim:opendkim /etc/opendkim/keys/
    echo "DKIM key generated."
else
    echo "DKIM key already exists, skipping generation."
fi

# ---------------------------------------------------------------------------
# 5. Configure OpenDKIM
# ---------------------------------------------------------------------------
cat > /etc/opendkim.conf << EOF
Domain          ${DOMAIN}
KeyFile         ${KEY_DIR}/${SELECTOR}.private
Selector        ${SELECTOR}
Socket          local:${OPENDKIM_SOCK}
UserID          opendkim
UMask           007
EOF

# Leave /etc/default/opendkim's SOCKET line in control — it points to the
# same /run/opendkim/opendkim.sock path that Postfix is configured to use.

# ---------------------------------------------------------------------------
# 6. Start / restart services
# ---------------------------------------------------------------------------
systemctl enable --now opendkim
systemctl restart opendkim
systemctl enable --now postfix
systemctl restart postfix

# ---------------------------------------------------------------------------
# 7. Print DNS records to add manually
# ---------------------------------------------------------------------------
DKIM_P=$(grep -o '"p=[^"]*"' "${KEY_DIR}/${SELECTOR}.txt" | tr -d '"' | sed 's/p=//')
# The key file may split p= across two quoted strings — handle that
DKIM_P=$(awk '/"p=/{found=1} found{gsub(/[" \t]|^\s+/,""); printf $0} /\)/{if(found)exit}' "${KEY_DIR}/${SELECTOR}.txt" | sed 's/p=//')

echo ""
echo "============================================================"
echo "  Add these DNS records in GoDaddy before sending mail"
echo "============================================================"
echo ""
echo "1. SPF (TXT record)"
echo "   Name:  @"
echo "   Value: v=spf1 ip4:${SERVER_IP} -all"
echo ""
echo "2. DKIM (TXT record)"
echo "   Name:  ${SELECTOR}._domainkey"
echo "   Value: v=DKIM1; h=sha256; k=rsa; p=${DKIM_P}"
echo ""
echo "3. PTR / Reverse DNS"
echo "   Set in your VPS control panel (Linode):"
echo "   IP ${SERVER_IP} → ${DOMAIN}"
echo ""
echo "Once DNS propagates, test with:"
echo "  echo 'Test' | mail -s 'Postfix test' you@example.com"
echo "  tail -f /var/log/mail.log"
