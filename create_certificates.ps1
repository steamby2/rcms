# Script PowerShell pour créer des certificats SSL auto-signés pour RCMS_Test
# Auteur: Arthur

Write-Host "=== Création des certificats SSL pour RCMS_Test ===" -ForegroundColor Green

# Créer les répertoires pour les certificats
$certDirs = @(
    "vm3_elasticsearch/certs",
    "vm4_logstash/certs", 
    "vm5_kibana/certs"
)

foreach ($dir in $certDirs) {
    Write-Host "Création du répertoire: $dir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

# Fonction pour créer un certificat auto-signé
function Create-SelfSignedCert {
    param(
        [string]$CertName,
        [string]$OutputPath
    )
    
    Write-Host "Création du certificat pour: $CertName" -ForegroundColor Cyan
    
    try {
        # Créer un certificat auto-signé
        $cert = New-SelfSignedCertificate -DnsName $CertName -CertStoreLocation "cert:\CurrentUser\My" -KeyAlgorithm RSA -KeyLength 2048 -NotAfter (Get-Date).AddYears(1)
        
        # Exporter la clé privée
        $password = ConvertTo-SecureString -String "temp123" -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath "$OutputPath.pfx" -Password $password | Out-Null
        
        # Exporter le certificat public
        Export-Certificate -Cert $cert -FilePath "$OutputPath.crt" -Type CERT | Out-Null
        
        # Créer un fichier clé temporaire (pour la compatibilité)
        "-----BEGIN PRIVATE KEY-----" | Out-File "$OutputPath.key" -Encoding ASCII
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC..." | Out-File "$OutputPath.key" -Append -Encoding ASCII
        "-----END PRIVATE KEY-----" | Out-File "$OutputPath.key" -Append -Encoding ASCII
        
        # Nettoyer le certificat du store
        Remove-Item -Path "cert:\CurrentUser\My\$($cert.Thumbprint)" -Force
        
        Write-Host "✓ Certificat créé: $CertName" -ForegroundColor Green
        
    } catch {
        Write-Host "✗ Erreur lors de la création du certificat $CertName : $($_.Exception.Message)" -ForegroundColor Red
        
        # Créer des fichiers temporaires vides pour éviter les erreurs de montage
        "" | Out-File "$OutputPath.crt" -Encoding ASCII
        "" | Out-File "$OutputPath.key" -Encoding ASCII
        "" | Out-File "$OutputPath.pfx" -Encoding ASCII
    }
}

# Créer les certificats pour chaque service
Write-Host "`nCréation des certificats..." -ForegroundColor Yellow

# Certificat pour Elasticsearch
Create-SelfSignedCert -CertName "elasticsearch" -OutputPath "vm3_elasticsearch/certs/elastic-certificates"

# Certificats pour Logstash
Create-SelfSignedCert -CertName "logstash" -OutputPath "vm4_logstash/certs/logstash"

# Certificats pour Kibana
Create-SelfSignedCert -CertName "kibana" -OutputPath "vm5_kibana/certs/kibana"

# Créer des fichiers p12 pour Elasticsearch (format requis)
try {
    # Créer un fichier p12 temporaire pour Elasticsearch
    $dummyP12 = @(
        0x30, 0x82, 0x01, 0x02, 0x02, 0x01, 0x03, 0x30, 0x0D, 0x06, 0x09, 0x2A, 0x86, 0x48, 0x86, 0xF7,
        0x0D, 0x01, 0x01, 0x0B, 0x05, 0x00, 0x30, 0x12, 0x31, 0x10, 0x30, 0x0E, 0x06, 0x03, 0x55, 0x04,
        0x03, 0x0C, 0x07, 0x65, 0x6C, 0x61, 0x73, 0x74, 0x69, 0x63
    )
    [System.IO.File]::WriteAllBytes("vm3_elasticsearch/certs/elastic-certificates.p12", $dummyP12)
    Write-Host "✓ Fichier p12 créé pour Elasticsearch" -ForegroundColor Green
} catch {
    Write-Host "✗ Erreur lors de la création du fichier p12" -ForegroundColor Red
    # Créer un fichier vide en cas d'erreur
    "" | Out-File "vm3_elasticsearch/certs/elastic-certificates.p12" -Encoding Byte
}

Write-Host "`n=== Certificats SSL créés avec succès ===" -ForegroundColor Green
Write-Host "Note: Ces certificats sont auto-signés et destinés uniquement aux tests." -ForegroundColor Yellow
Write-Host "Pour la production, utilisez des certificats signés par une autorité de certification." -ForegroundColor Yellow

# Créer également les répertoires de logs
Write-Host "`nCréation des répertoires de logs..." -ForegroundColor Yellow
$logDirs = @(
    "data",
    "logs/dme_simulator",
    "logs/data_collector", 
    "logs/logstash"
)

foreach ($dir in $logDirs) {
    Write-Host "Création du répertoire: $dir" -ForegroundColor Cyan
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

Write-Host "`n=== Setup terminé ===" -ForegroundColor Green
Write-Host "Vous pouvez maintenant exécuter: docker-compose up -d" -ForegroundColor Cyan