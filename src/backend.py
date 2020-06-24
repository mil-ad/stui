import subprocess
import re
import shutil


class Cluster(object):
    def __init__(self, remote):
        super().__init__()

        if not remote:
            if shutil.which("sinfo") is None:
                raise SystemExit("Slurm binaries not found.")
        else:
            pass

        self.remote = remote

        self.me = None

        # self.nodes = get_nodes()
        self.partitions = None

        self.config = self.get_config()

    def run_command(self, cmd: str):
        if self.remote:
            cmd = " ".join(["ssh", self.remote, cmd])

        process = subprocess.run(cmd.split(" "), capture_output=True)
        o = process.stdout.decode("utf-8").splitlines()

        return o

    def get_config(self):
        return {"ClusterName": "foo"}
        o = self.run_command("scontrol show config")

        pattern = "(\S+)\s*=(.*)"

        config = {}
        for line in o[1:]:
            try:
                match = re.search(pattern, line)
                config[match.group(1)] = match.group(2)
            except:
                continue

        return config

    def get_jobs(self):
        return {"foo":"foo"}
        o = self.run_command("squeue")

        jobs = []
        fields = o[0].split()
        for line in o[1:]:
            job = {k: v for k, v in zip(fields, line.split())}
            jobs.append(Job(job))

        return jobs


class Partition(object):
    def __init__(self):
        super().__init__()


class Job(object):
    def __init__(self, string):
        super().__init__()

        self.job_id = string["JOBID"]
        self.nodes = string["NODES"]
        self.partition = string["PARTITION"]
        self.name = string["NAME"]
        self.user = string["USER"]
        self.state = string["ST"]
        # self.time

    def __repr__(self):
        return f"{self.job_id} User: {self.user} State: {self.state}"


class JobStep(object):
    def __init__(self):
        super().__init__()


class Node(object):
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    jobs = get_jobs()
    for j in jobs:
        print(j)
