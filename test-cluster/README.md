# Test Cluster

A Docker-based Slurm cluster for testing stui. Runs a real Slurm controller + 2 compute nodes with fake but realistic jobs from multiple users.

## Prerequisites

- Docker with compose plugin
- sudo access

## Quick Start

From the project root:

```bash
make rebuild        # build images and start cluster
make submit         # submit ~17 fake jobs
make squeue         # check the job queue
```

## Make Targets

```
make up             Start the cluster
make down           Stop the cluster
make rebuild        Rebuild images and start
make submit         Submit fake jobs
make squeue         Show job queue
make sinfo          Show node/partition status
make shell          Interactive shell on slurmctld
make logs           Tail all container logs
make logs-ctrl      Tail slurmctld logs only
make clean          Stop cluster, remove volumes and images
```

## Cluster Layout

| Service | Role | Hostname |
|---|---|---|
| slurmctld | Controller | slurmctld |
| node1 | Compute | node1 |
| node2 | Compute | node2 |

**Partitions:** `compute` (default), `gpu`

**Users:** `alice`, `bob`, `carol`, `dave`

## Fake Jobs

| User | Jobs | Script |
|---|---|---|
| alice | ML training (BERT, ViT, GPT-2) | `model_training.py` — training logs with loss/accuracy, gradient warnings |
| bob | Genome alignment | `genome_align.sh` — BWA-MEM2 style output, mapping quality warnings |
| carol | Data ETL + array job | `data_pipeline.sh` — progress bars, schema warnings, null values |
| dave | Matrix computation + failing jobs | `matrix_multiply.py` — GFLOPS/ETA display; `failed_job.py` — realistic crashes (OOM, CUDA, KeyError, timeout) |

Jobs are lightweight (sleep + print loops) and finish within a few minutes. Failed jobs crash after ~30 seconds with realistic Python tracebacks.

## Approximate Job Runtimes

| Script | Duration |
|---|---|
| `model_training.py` | 15-60 min |
| `data_pipeline.sh` | ~3 min |
| `genome_align.sh` | ~1-2 min |
| `matrix_multiply.py` | ~1-3 min |
| `failed_job.py` | ~30s-1 min (then crashes) |
| quick-test / sanity-check | ~5s |
