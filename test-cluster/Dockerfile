FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
        slurm-wlm slurm-client \
        munge libmunge-dev \
        python3 \
        procps iproute2 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# State dirs
RUN mkdir -p /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm /run/munge && \
    chown slurm:slurm /var/spool/slurmctld /var/spool/slurmd /var/log/slurm /var/run/slurm

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
COPY cgroup.conf /etc/slurm/cgroup.conf
RUN chmod 644 /etc/slurm/slurm.conf /etc/slurm/cgroup.conf
COPY fake_jobs/ /opt/fake_jobs/
COPY submit_fake_jobs.sh /opt/submit_fake_jobs.sh
RUN chmod +x /opt/submit_fake_jobs.sh /opt/fake_jobs/*.sh 2>/dev/null; \
    chmod +r /opt/fake_jobs/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
