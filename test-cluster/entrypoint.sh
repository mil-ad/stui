#!/bin/bash
set -euo pipefail

append_if_missing() {
    local line=$1
    local file=$2
    grep -qF "$line" "$file" 2>/dev/null || echo "$line" >> "$file"
}

wait_for_port() {
    local host=$1
    local port=$2
    local name=$3
    echo "Waiting for $name to be ready..."
    while ! nc -z "$host" "$port" 2>/dev/null; do
        sleep 1
    done
}

patch_node_conf() {
    # Patch slurm.conf with actual hardware so slurmd doesn't reject mismatched config
    local cpus mem sockets cores threads
    cpus=$(nproc)
    mem=$(awk '/MemTotal/{printf "%d", $2/1024}' /proc/meminfo)
    sockets=$(lscpu | awk '/^Socket\(s\)/{print $2}')
    cores=$(lscpu | awk '/^Core\(s\) per socket/{print $4}')
    threads=$(lscpu | awk '/^Thread\(s\) per core/{print $4}')
    sed -i "s/^NodeName=node\\[1-2\\] .*/NodeName=node[1-2] CPUs=$cpus Sockets=$sockets CoresPerSocket=$cores ThreadsPerCore=$threads RealMemory=$mem State=UNKNOWN/" /etc/slurm/slurm.conf
}

# Fix munge permissions — use force flag to handle rootless podman uid mapping
chown munge:munge /etc/munge/munge.key /run/munge 2>/dev/null || true
chmod 400 /etc/munge/munge.key
chmod 755 /run/munge

# Start munge (--force allows running even if file ownership looks wrong under uid mapping)
runuser -u munge -- munged --force

ROLE=${SLURM_ROLE:-slurmd}
patch_node_conf

if [ "$ROLE" = "slurmdbd" ]; then
    wait_for_port mysql 3306 "MySQL"
    sleep 2  # Extra time for MySQL to fully initialize
    echo "Starting slurmdbd..."
    exec slurmdbd -D
elif [ "$ROLE" = "slurmctld" ]; then
    wait_for_port slurmdbd 6819 "slurmdbd"
    echo "Starting slurmctld..."
    exec slurmctld -D
elif [ "$ROLE" = "slurmd" ]; then
    echo "Starting slurmd on $(hostname)..."
    exec slurmd -D
elif [ "$ROLE" = "slurmrestd" ]; then
    wait_for_port slurmctld 6817 "slurmctld"
    echo "Starting slurmrestd..."
    # Add Docker gateway to /etc/hosts and reduce DNS timeout to prevent
    # slow reverse lookups on client IPs (default glibc timeout is 5s × 2 attempts = 10s)
    GATEWAY=$(ip route | awk '/default/{print $3}')
    if [ -n "$GATEWAY" ]; then
        append_if_missing "$GATEWAY dockerhost" /etc/hosts
    fi
    append_if_missing "options single-request-reopen timeout:1 attempts:1" /etc/resolv.conf
    chown slurmrest:slurmrest /var/run/slurmrestd
    # SLURM_JWT=daemon is required for slurmrestd to accept JWT authentication
    export SLURM_JWT=daemon
    exec gosu slurmrest /usr/sbin/slurmrestd -t 4 -a rest_auth/jwt 0.0.0.0:6820
else
    echo "Unknown role: $ROLE"
    exit 1
fi
