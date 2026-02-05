FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
        slurm-wlm slurm-client slurmdbd slurmrestd \
        munge libmunge-dev \
        mariadb-client \
        libjwt0 \
        python3 \
        gosu netcat-openbsd \
        procps iproute2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create slurmrest user for REST API (must not be root or slurm)
RUN groupadd -r slurmrest && useradd -r -g slurmrest slurmrest

# State dirs
RUN mkdir -p /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm /run/munge /var/run/slurmrestd && \
    chown slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm && \
    chown slurmrest:slurmrest /var/run/slurmrestd

# Create dummy users
RUN useradd -m alice && \
    useradd -m bob && \
    useradd -m carol && \
    useradd -m dave

# Shared munge key
RUN dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key 2>/dev/null && \
    chown munge:munge /etc/munge/munge.key && \
    chmod 400 /etc/munge/munge.key

COPY slurm.conf /etc/slurm/slurm.conf
COPY slurmdbd.conf /etc/slurm/slurmdbd.conf
COPY cgroup.conf /etc/slurm/cgroup.conf
COPY jwt.key /etc/slurm/jwt.key

# JWT key needs to be readable by slurm (slurmctld) and slurmrest (slurmrestd)
RUN chown slurm:slurmrest /etc/slurm/jwt.key && \
    chmod 640 /etc/slurm/jwt.key && \
    chmod 644 /etc/slurm/slurm.conf /etc/slurm/cgroup.conf && \
    chmod 600 /etc/slurm/slurmdbd.conf && \
    chown slurm:slurm /etc/slurm/slurmdbd.conf
COPY fake_jobs/ /opt/fake_jobs/
COPY submit_fake_jobs.sh /opt/submit_fake_jobs.sh
RUN chmod +x /opt/submit_fake_jobs.sh /opt/fake_jobs/*.sh 2>/dev/null; \
    chmod +r /opt/fake_jobs/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
