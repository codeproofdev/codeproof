#!/bin/bash
# CodeProof Docker Entrypoint - Initialize isolate sandbox

set -e

echo "================================================"
echo "CodeProof Judge System - Starting"
echo "================================================"

# ============================================
# SETUP ISOLATE CGROUPS
# ============================================
echo "Setting up isolate sandbox..."

# Create isolate run directory
echo "Preparing isolate directories..."
mkdir -p /run/isolate 2>/dev/null || true

# Create isolate boxes directory
mkdir -p /var/local/lib/isolate
chmod 755 /var/local/lib/isolate

# Configure isolate to use container's cgroup (not host daemon)
# Inside Docker, isolate will create boxes directly under /sys/fs/cgroup
echo "Configuring isolate cgroup..."

# In Docker with cgroups v2, we use the root cgroup directly
# Isolate will create /sys/fs/cgroup/box-N directories as needed
echo "/sys/fs/cgroup" > /run/isolate/cgroup
echo "✓ Isolate configured to use container cgroup (v2)"

# Test isolate
echo "Testing isolate..."
if isolate --version > /dev/null 2>&1; then
    echo "✓ Isolate is available"
    isolate --version
else
    echo "✗ WARNING: Isolate not available"
fi

# Test a simple isolate command with cgroups
echo "Testing isolate sandbox..."
if isolate --cg --box-id=0 --init > /dev/null 2>&1; then
    echo "✓ Isolate sandbox initialized successfully with cgroups"
    isolate --cg --box-id=0 --cleanup > /dev/null 2>&1
else
    echo "✗ WARNING: Isolate sandbox initialization failed"
    echo "  This container needs --privileged flag or --cap-add SYS_ADMIN"
    echo "  Trying without --cg flag..."
    if isolate --box-id=0 --init > /dev/null 2>&1; then
        echo "✓ Isolate works without cgroups (limited functionality)"
        isolate --box-id=0 --cleanup > /dev/null 2>&1
    else
        echo "✗ Isolate completely failed"
    fi
fi

# ============================================
# VERIFY COMPILERS
# ============================================
echo ""
echo "Verifying compilers..."

# Python
if command -v python3.10 &> /dev/null; then
    echo "✓ Python $(python3.10 --version)"
else
    echo "✗ Python 3.10 not found"
fi

# C++
if command -v g++-12 &> /dev/null; then
    echo "✓ G++ $(g++-12 --version | head -1)"
else
    echo "✗ G++ not found"
fi

# Rust
if command -v rustc &> /dev/null; then
    echo "✓ Rust $(rustc --version)"
else
    echo "✗ Rust not found"
fi

# Node.js
if command -v node &> /dev/null; then
    echo "✓ Node.js $(node --version)"
else
    echo "✗ Node.js not found"
fi

# Go
if command -v go &> /dev/null; then
    echo "✓ Go $(go version | awk '{print $3}')"
else
    echo "✗ Go not found"
fi

# ============================================
# RUN MIGRATIONS (if backend service)
# ============================================
if [ "$1" = "uvicorn" ]; then
    echo ""
    echo "Running database migrations..."
    # Wait for database to be ready
    echo "Waiting for database..."
    sleep 5

    # Run migrations if alembic is available
    if command -v alembic &> /dev/null; then
        echo "Running alembic migrations..."
        alembic upgrade head || echo "⚠ Migrations failed or not needed"
    fi
fi

echo ""
echo "================================================"
echo "Starting application: $@"
echo "================================================"
echo ""

# Execute the main command
exec "$@"
