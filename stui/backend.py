import subprocess
import re
import shutil
import threading
from time import sleep

import fabric


class Cluster(object):
    def __init__(self, remote):
        super().__init__()

        self.use_fabric = True

        if not remote:
            if shutil.which("sinfo") is None:
                raise SystemExit("Slurm binaries not found.")
        elif self.use_fabric:
            self.fabric_connection = fabric.Connection(remote)

        self.remote = remote

        self.me = self.run_command("whoami")[0]  ## TODO

        self.partitions = None

        self.config = self.get_config()

        self.my_partitions, self.all_partitions = self.get_partition_info()

        self.latest_jobs = []
        self.thread = threading.Thread(target=self.thread_fn, daemon=True)
        self.thread.start()

    def thread_fn(self):
        while True:
            self.latest_jobs = self._get_jobs()
            sleep(1)

    def run_command(self, cmd: str):
        if self.remote:
            if self.use_fabric:
                results = self.fabric_connection.run(cmd, hide=True)
                o = results.stdout.splitlines()
            else:
                cmd = f"ssh {self.remote} {cmd}"
                process = subprocess.run(cmd.split(" "), capture_output=True)
                o = process.stdout.decode("utf-8").splitlines()
        else:
            process = subprocess.run(cmd.split(" "), capture_output=True)
            o = process.stdout.decode("utf-8").splitlines()

        return o

    def get_config(self):
        o = self.run_command("scontrol show config")

        pattern = r"(\S+)\s*=(.*)"

        config = {}
        for line in o[1:]:
            try:
                match = re.search(pattern, line)
                config[match.group(1)] = match.group(2)
            except:
                continue

        return config

    def get_partition_info(self):

        my_p = self.run_command('sinfo --format="%R" --noheader')
        all_p = self.run_command('sinfo --format="%R" --noheader --all')

        return my_p, all_p

    def get_jobs(self):
        # TODO Acquire a lock a return a clone?
        return self.latest_jobs

    def _get_jobs(self):
        cmd = 'squeue --all --format="%A|%C|%b|%F|%K|%j|%P|%r|%u|%y|%T|%M|%b|%N"'
        o = self.run_command(cmd)

        jobs = []
        fields = o[0].split("|")
        for line in o[1:]:
            job = {k: v for k, v in zip(fields, line.split("|"))}
            jobs.append(Job(job))

        return jobs

    def cancel_jobs(self, jobs):
        job_ids = " ".join([j.job_id] for j in jobs)
        self.run_command(f"scancel {job_ids}")

    def cancel_my_jobs(self):
        self.run_command(f"scancel -u {self.me}")


    def get_name(self):
        return self.config["ClusterName"]


class Job(object):
    def __init__(self, string):
        super().__init__()

        self.job_id = string["JOBID"]
        self.nodes = string["NODELIST"].split(",")
        self.partition = string["PARTITION"]
        self.name = string["NAME"]
        self.user = string["USER"]
        self.state = string["STATE"]
        self.time = string["TIME"]
        self.nice = string["NICE"]
        self.cpus = string["CPUS"]
        self.gres = string["GRES"] if "GRES" in string else None

        self.array_base_id = string["ARRAY_JOB_ID"]
        self.array_task_id = string["ARRAY_TASK_ID"]

        self.is_array_job = False if self.array_task_id == "N/A" else True

        if self.is_array_job and "%" in self.array_task_id:
            match = re.search(r"\d+%(\d+)", self.array_task_id)
            self.array_throttle = match.group(1)
        else:
            self.array_throttle = None

    def __repr__(self):
        return f"Job {self.job_id} - State{self.state}"

    def is_running(self):
        return self.state == "RUNNING"

    def uses_gpu(self):
        return "gpu" in self.gres
