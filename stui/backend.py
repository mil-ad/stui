import copy
import functools
import os
import re
import shutil
import subprocess
import threading
from queue import Queue
from time import sleep

import fabric

__all__ = ["Cluster"]


def when_connected(deocrated_f):
    @functools.wraps(deocrated_f)
    def f(self, *args, **kwargs):
        if not self.is_ready.is_set():
            raise EnvironmentError  # TODO: Use a sensible exception

        return deocrated_f(self, *args, **kwargs)

    return f


class Cluster(object):
    def __init__(self, remote=None):
        super().__init__()

        self.use_fabric = True
        self.remote = remote

        self.is_ready = threading.Event()

        self.latest_jobs = []
        self.thread = threading.Thread(target=self._thread_fn, daemon=True)

        self.lock = threading.Lock()
        self.requests = Queue()

    def connect(self, fd):
        self.fd = fd
        self.thread.start()

    def _thread_fn(self):

        if self.remote is None:
            if shutil.which("sinfo") is None:
                # TODO: Test this!
                raise SystemExit("Slurm binaries not found.")
        elif self.use_fabric:
            self.fabric_connection = fabric.Connection(self.remote)
            self.fabric_connection.open()

        self.me = self._run_command("whoami")[0]  # TODO
        self.config = self._get_config()
        self.my_partitions, self.all_partitions = self._get_partition_info()

        self.is_ready.set()
        os.write(self.fd, b"connection established")
        os.close(self.fd)
        self.fd = None

        while True:
            try:
                latest_jobs = self._get_jobs()
                with self.lock:
                    self.latest_jobs = latest_jobs

                if not self.requests.empty():
                    cmd = self.requests.get(block=False)
                    self._run_command(cmd)

                sleep(1)

            except (
                EOFError,
                OSError,
            ):
                # TODO:: Where's the best place to do error handing
                with self.lock:
                    self.fabric_connection = fabric.Connection(self.remote)
                    self.fabric_connection.open()

    def _run_command(self, cmd: str):
        if self.remote is not None:
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

    def _get_config(self):
        o = self._run_command("scontrol show config")

        pattern = r"(\S+)\s*=(.*)"

        config = {}
        for line in o[1:]:
            try:
                match = re.search(pattern, line)
                config[match.group(1)] = match.group(2)
            except:
                continue

        return config

    def _get_partition_info(self):

        my_p = self._run_command('sinfo --format="%R" --noheader')
        all_p = self._run_command('sinfo --format="%R" --noheader --all')

        return my_p, all_p

    def _get_jobs(self):
        cmd = 'squeue --all --format="%A|%C|%b|%F|%K|%j|%P|%r|%u|%y|%T|%M|%b|%N"'
        o = self._run_command(cmd)

        jobs = []
        fields = o[0].split("|")
        for line in o[1:]:
            job = {k: v for k, v in zip(fields, line.split("|"))}
            jobs.append(Job(job))

        return jobs

    @when_connected
    def get_name(self):
        return self.config["ClusterName"]

    @when_connected
    def get_jobs(self):
        with self.lock:
            jobs_copy = copy.deepcopy(self.latest_jobs)
        return jobs_copy

    @when_connected
    def cancel_jobs(self, jobs):
        job_ids = " ".join(str(j.job_id) for j in jobs)
        self.requests.put(f"scancel {job_ids}")

    @when_connected
    def cancel_my_jobs(self):
        self.requests.put(f"scancel -u {self.me}")

    @when_connected
    def cancel_my_newest_job(self):
        self.requests.put(
            f'squeue -u {self.me} --sort=-V -h --format="%A" | head -n 1 | xargs scancel'
        )

    @when_connected
    def cancel_my_oldest_job(self):
        self.requests.put(
            f'squeue -u {self.me} --sort=+V -h --format="%A" | head -n 1 | xargs scancel'
        )


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
