#!/bin/bash
# Script de hardening pour les machines virtuelles du projet RCMS_Test
# Ce script applique les mesures de sécurité de base pour renforcer la sécurité des VM
# Auteur: Arthur

# Fonction pour afficher les messages avec horodatage
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Vérification des privilèges root
if [ "$(id -u)" -ne 0 ]; then
    log "Ce script doit être exécuté avec les privilèges root"
    exit 1
fi

# Mise à jour du système
log "Mise à jour du système..."
apt-get update -y
apt-get upgrade -y

# Installation des outils de sécurité essentiels
log "Installation des outils de sécurité..."
apt-get install -y ufw fail2ban rkhunter lynis unattended-upgrades apt-listchanges apparmor apparmor-utils auditd

# Configuration du pare-feu UFW
log "Configuration du pare-feu UFW..."
ufw default deny incoming
ufw default allow outgoing

# Configuration spécifique selon le type de VM
VM_TYPE=$1

case $VM_TYPE in
    "dme_simulator")
        log "Configuration pour le simulateur DME (VM1)..."
        # Ouverture du port pour l'API REST
        ufw allow 5000/tcp comment "DME Simulator API"
        ;;
    "data_collector")
        log "Configuration pour le collecteur de données (VM2)..."
        # Pas de ports entrants nécessaires
        ;;
    "elasticsearch")
        log "Configuration pour Elasticsearch (VM3)..."
        ufw allow 9200/tcp comment "Elasticsearch API"
        ufw allow 9300/tcp comment "Elasticsearch Node Communication"
        ;;
    "logstash")
        log "Configuration pour Logstash (VM4)..."
        ufw allow 5044/tcp comment "Logstash Beats Input"
        ;;
    "kibana")
        log "Configuration pour Kibana (VM5)..."
        ufw allow 5601/tcp comment "Kibana Web Interface"
        ;;
    *)
        log "Type de VM non reconnu. Utilisation: $0 [dme_simulator|data_collector|elasticsearch|logstash|kibana]"
        exit 1
        ;;
esac

# Activation du pare-feu
log "Activation du pare-feu..."
ufw --force enable

# Configuration de Fail2ban
log "Configuration de Fail2ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

# Redémarrage de Fail2ban
systemctl restart fail2ban

# Configuration des mises à jour automatiques
log "Configuration des mises à jour automatiques..."
cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# Durcissement SSH
log "Durcissement de la configuration SSH..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
cat > /etc/ssh/sshd_config << EOF
# Configuration SSH sécurisée
Port 22
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
UsePrivilegeSeparation yes
KeyRegenerationInterval 3600
ServerKeyBits 2048
SyslogFacility AUTH
LogLevel INFO
LoginGraceTime 120
PermitRootLogin no
StrictModes yes
RSAAuthentication yes
PubkeyAuthentication yes
IgnoreRhosts yes
RhostsRSAAuthentication no
HostbasedAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
PasswordAuthentication yes
X11Forwarding no
X11DisplayOffset 10
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
UsePAM yes
AllowUsers ubuntu
MaxAuthTries 3
MaxSessions 5
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

# Redémarrage du service SSH
systemctl restart sshd

# Configuration des limites de ressources système
log "Configuration des limites de ressources système..."
cat > /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 4096
* hard nproc 4096
EOF

# Configuration de l'audit système
log "Configuration de l'audit système..."
cat > /etc/audit/rules.d/audit.rules << EOF
# Surveillance des modifications de fichiers critiques
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k identity

# Surveillance des appels système critiques
-a always,exit -F arch=b64 -S execve -k exec
-a always,exit -F arch=b32 -S execve -k exec

# Surveillance des modifications de la configuration réseau
-w /etc/network/ -p wa -k network
-w /etc/hosts -p wa -k network
EOF

# Redémarrage du service d'audit
systemctl restart auditd

# Durcissement des paramètres du noyau
log "Durcissement des paramètres du noyau..."
cat > /etc/sysctl.d/99-security.conf << EOF
# Protection contre les attaques de type IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Désactivation du routage IP
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Protection contre les attaques SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# Ignorer les pings (protection contre les attaques ICMP)
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_echo_ignore_all = 0

# Protection contre les attaques SMURF
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Désactivation des redirections ICMP
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Protection de la mémoire
kernel.randomize_va_space = 2
EOF

# Application des paramètres du noyau
sysctl -p /etc/sysctl.d/99-security.conf

# Création d'un utilisateur non privilégié pour les services
log "Création d'un utilisateur de service..."
useradd -r -s /bin/false -m -d /opt/rcms rcms_service

# Configuration des permissions restrictives pour les fichiers de configuration
log "Configuration des permissions restrictives..."
chmod 750 /opt/rcms
chown rcms_service:rcms_service /opt/rcms

# Exécution d'un scan de sécurité avec Lynis
log "Exécution d'un scan de sécurité avec Lynis..."
lynis audit system --quick

log "Hardening terminé pour $VM_TYPE"
exit 0
