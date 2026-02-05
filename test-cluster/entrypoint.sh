#!/bin/bash
set -e

# Fix munge permissions — use force flag to handle rootless podman uid mapping
chown munge:munge /etc/munge/munge.key /run/munge 2>/dev/null || true
chmod 400 /etc/munge/munge.key
chmod 755 /run/munge

# Start munge (--force allows running even if file ownership looks wrong under uid mapping)
runuser -u munge -- munged --force

ROLE=${SLURM_ROLE:-slurmd}

# Patch slurm.conf with actual hardware so slurmd doesn't reject mismatched config
CPUS=$(nproc)
MEM=$(awk '/MemTotal/{printf "%d", $2/1024}' /proc/meminfo)
SOCKETS=$(lscpu | awk '/^Socket\(s\)/{print $2}')
CORES=$(lscpu | awk '/^Core\(s\) per socket/{print $4}')
THREADS=$(lscpu | awk '/^Thread\(s\) per core/{print $4}')
sed -i "s/^NodeName=node\[1-2\] .*/NodeName=node[1-2] CPUs=$CPUS Sockets=$SOCKETS CoresPerSocket=$CORES ThreadsPerCore=$THREADS RealMemory=$MEM State=UNKNOWN/" /etc/slurm/slurm.conf

if [ "$ROLE" = "slurmdbd" ]; then
    echo "Waiting for MySQL to be ready..."
    while ! nc -z mysql 3306 2>/dev/null; do
        sleep 1
    done
    sleep 2  # Extra time for MySQL to fully initialize
    echo "Starting slurmdbd..."
    exec slurmdbd -D -vv
elif [ "$ROLE" = "slurmctld" ]; then
    echo "Waiting for slurmdbd to be ready..."
    while ! nc -z slurmdbd 6819 2>/dev/null; do
        sleep 1
    done
    echo "Starting slurmctld..."
    exec slurmctld -D -vv
elif [ "$ROLE" = "slurmd" ]; then
    echo "Starting slurmd on $(hostname)..."
    exec slurmd -D -vv
elif [ "$ROLE" = "slurmrestd" ]; then
    echo "Waiting for slurmctld to be ready..."
    while ! nc -z slurmctld 6817 2>/dev/null; do
        sleep 1
    done
    echo "Starting slurmrestd..."
    chown slurmrest:slurmrest /var/run/slurmrestd
    # SLURM_JWT=daemon is required for slurmrestd to accept JWT authentication
    export SLURM_JWT=daemon
    exec gosu slurmrest /usr/sbin/slurmrestd -vv -a rest_auth/jwt 0.0.0.0:6820
else
    echo "Unknown role: $ROLE"
    exit 1
fi
