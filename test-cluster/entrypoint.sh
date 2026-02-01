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

if [ "$ROLE" = "slurmctld" ]; then
    echo "Starting slurmctld..."
    exec slurmctld -D -vv
elif [ "$ROLE" = "slurmd" ]; then
    echo "Starting slurmd on $(hostname)..."
    exec slurmd -D -vv
else
    echo "Unknown role: $ROLE"
    exit 1
fi
