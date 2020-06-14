import subprocess

class Cluster(object):
    def __init__(self):
        super().__init__()

        self.me = None

        # self.nodes = get_nodes()
        self.partitions = None

class Partition(object):
    def __init__(self):
        super().__init__()

class Job(object):
    def __init__(self):
        super().__init__()

        self.state = None

class JobStep(object):
    def __init__(self):
        super().__init__()

class Node(object):
    def __init__(self):
        super().__init__()



def squeue_loop():
    command = "ssh yarin squeue"
    squeue_process = subprocess.run(command.split(" "), capture_output=True)

    o = squeue_process.stdout.decode("utf-8").splitlines()

    jobs = []
    fields = o[0].split()
    for line in o[1:]:
        job = {k: v for k, v in zip(fields, line.split())}
        jobs.append(job)

    return jobs
