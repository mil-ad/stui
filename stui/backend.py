import copy
import functools
import logging
import os
import re
import shutil
import subprocess
import threading
from collections import OrderedDict
from queue import Queue
from time import sleep
from typing import Iterable, List

import fabric
from paramiko.ssh_exception import SSHException

__all__ = ["Cluster"]

logger = logging.getLogger("stui.backend")


def when_connected(deocrated_f):
    @functools.wraps(deocrated_f)
    def f(self, *args, **kwargs):
        if not self.is_ready.is_set():
            raise EnvironmentError  # TODO: Use a sensible exception

        return deocrated_f(self, *args, **kwargs)

    return f


class Job(object):
    def __init__(self, fields: Iterable[str], squeue_str: str):
        super().__init__()

        self.whole_line = squeue_str
        squeue_dict = {k: v for k, v in zip(fields, squeue_str.split("|"))}

        self.job_id = squeue_dict["job_id_unique"]
        self.job_id_combined = squeue_dict["job_id_base_idx"]
        self.job_id_base = squeue_dict["job_id_base"]
        self.job_id_idx = squeue_dict["job_id_idx"]

        self.nodes = squeue_dict["nodes"].split(",")
        self.partition = squeue_dict["partition"]
        self.name = squeue_dict["job_name"]
        self.user = squeue_dict["user"]
        self.state = squeue_dict["state"]
        self.time = squeue_dict["time"]
        self.nice = squeue_dict["nice"]
        self.cpus = squeue_dict["cpus"]
        self.gres = squeue_dict["tres"]

        self.is_array_job = False if self.job_id_idx == "N/A" else True

        self.array_total_jobs = None
        self.array_throttle = None
        if self.is_array_job and self.is_pending():
            if "%" in self.job_id_idx:
                match = re.search(r"(\d+)%(\d+)$", self.job_id_idx)
                if match:
                    self.array_total_jobs = match.group(1)
                    self.array_throttle = match.group(2)
            else:
                # TODO: are there [ ]s?
                match = re.search(r"_\[(\d+)\]$", self.job_id_idx)
                if match:
                    self.array_total_jobs = match.group(1)

    def __repr__(self):
        return f"Job {self.job_id} - State{self.state}"

    def is_running(self):
        return self.state == "RUNNING"

    def is_pending(self):
        return self.state == "PENDING"

    def uses_gpu(self):
        return "gpu" in self.gres

    def is_array_job_f(self):
        return self.is_array_job  # TODO: use property?

    def array_str(self):
        if not self.is_array_job:
            return ""
        else:
            return self.job_id_idx


class Cluster(threading.Thread):
    def __init__(self, remote=None):
        super().__init__()

        self.use_fabric = True
        self.remote = remote

        self.is_ready = threading.Event()

        self.latest_jobs = []

        self.lock = threading.Lock()
        self.requests = Queue()
        self.thread = None

    def connect(self, fd, ssh_username=None, ssh_password=None):
        self.fd = fd
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password

        if self.thread is not None:
            self.thread.join()
        self.thread = threading.Thread(target=self._thread_fn, daemon=True)
        self.thread.start()

    def _thread_fn(self):

        if self.remote is None:
            if shutil.which("sinfo") is None:
                # TODO: Test this!
                raise SystemExit("Slurm binaries not found.")
        elif self.use_fabric:
            connect_kwargs = {
                "password": self.ssh_password,
                "look_for_keys": True,
                "allow_agent": True,
                "auth_timeout": 10,
                "timeout": 5,
            }
            self.fabric_connection = fabric.Connection(
                self.remote, user=self.ssh_username, connect_kwargs=connect_kwargs
            )

            try:
                self.fabric_connection.open()
            except SSHException as e:
                if str(e) == "No authentication methods available":
                    os.write(self.fd, b"need password")
                elif str(e) == "Authentication failed.":
                    os.write(self.fd, b"wrong password")
                else:
                    raise SystemExit("Lost SSH connection.")
                return

        self.me = self._run_command("whoami")[0]  # TODO
        self.config = self._get_config()
        self.my_partitions, self.all_partitions = self._get_partition_info()

        self.is_ready.set()
        os.write(self.fd, b"connection established")
        os.close(self.fd)
        self.fd = None

        try:
            while True:
                latest_jobs = self._get_jobs()
                with self.lock:
                    self.latest_jobs = latest_jobs
                if not self.requests.empty():
                    cmd = self.requests.get(block=False)
                    self._run_command(cmd)

                sleep(1)
        except:
            # if self.remote:
            #     self.fabric_connection.close()
            #     self.fabric_connection = fabric.Connection(self.remote)
            #     self.fabric_connection.open()
            raise SystemExit("Something went wrong.")

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
            # TODO: for some reason lines are surrounded by quotes when not using SSH
            o = [line.strip('"') for line in o]

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

    def _get_jobs(self) -> List[Job]:
        """
        squeue has two formatting commands: --format and --Format (-o and -O). The
        former is more flexible in terms of constructing a string but it uses single
        letters for each field and slurm devs eventually ran out of letters to use! I
        think going forward they want peopel to use the long format. Some of the short
        format flags are not even documented, including the %b which I use is used to
        display TRES_PER_NODE. However, I prefer to use the short format because I can
        put my own delimeter character. It also assigns as many characters as needed to
        fully display a field. --Format on the other hand assigns 20 characters by
        default although you can specify more.

        Returns: List[Job]
        """

        fields = OrderedDict(
            {
                "job_id_unique": r"%A",  # for job arrays this will have a unique value for each element
                "job_id_base_idx": r"%i",  # for job arrays has the form "<base_job_id>_<index>"
                "job_id_base": r"%F",  # Job array's base job ID. For non-array jobs, this is the job ID
                "job_id_idx": r"%K",  # Job array's index
                "cpus": r"%C",
                "job_name": r"%j",
                "partition": r"%P",
                "reason": r"%r",
                "user": r"%u",
                "nice": r"%y",
                "state": r"%T",
                "time": r"%M",
                "tres": r"%b",
                "nodes": r"%N",
            }
        )

        cmd = f'squeue --noheader --all --format="{"|".join(fields.values())}"'
        cmd_output = self._run_command(cmd)

        return [Job(fields.keys(), line) for line in cmd_output]

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
