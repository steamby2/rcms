#!/bin/bash
echo "=== Test de build RCMS_Test ==="

echo "1. Test du build VM1..."
if docker build -t test-vm1 vm1_dme_simulator/; then
    echo "  ✓ VM1 build réussi"
    docker rmi test-vm1 2>/dev/null || true
else
    echo "  ✗ VM1 build échoué - essai avec Dockerfile minimal"
    if [ -f "vm1_dme_simulator/Dockerfile.minimal" ]; then
        cp vm1_dme_simulator/Dockerfile.minimal vm1_dme_simulator/Dockerfile
        echo "  → Dockerfile minimal activé pour VM1"
    fi
fi

echo "2. Test du build VM2..."
if docker build -t test-vm2 vm2_data_collector/; then
    echo "  ✓ VM2 build réussi"
    docker rmi test-vm2 2>/dev/null || true
else
    echo "  ✗ VM2 build échoué - essai avec Dockerfile minimal"
    if [ -f "vm2_data_collector/Dockerfile.minimal" ]; then
        cp vm2_data_collector/Dockerfile.minimal vm2_data_collector/Dockerfile
        echo "  → Dockerfile minimal activé pour VM2"
    fi
fi

echo "3. Build complet avec docker-compose..."
docker-compose build --no-cache
