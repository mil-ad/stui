# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

stui is a terminal-based Slurm cluster dashboard. The project is being rewritten from Python/urwid to Go/Bubbletea (current branch: v2). The original Python implementation is preserved in `stui-old-py/` for reference.

## Build & Run

```bash
go build              # Build the binary
./stui                # Run the application
```

## Test Cluster

A Docker-based Slurm cluster is provided for testing. Requires sudo for Docker commands.

```bash
make up               # Start the test cluster
make submit           # Submit ~17 fake jobs from multiple users
make squeue           # Show job queue
make sinfo            # Show node/partition status
make shell            # Interactive shell on slurmctld
make logs             # Tail all container logs
make down             # Stop the cluster
make clean            # Stop and remove volumes/images
make rest-token       # Generate JWT token for REST API
```

## Architecture

**TUI Framework:** Uses Charmbracelet's Bubbletea with the Elm-style architecture:
- `model` struct holds application state
- `Init()` returns initial command (fetches cluster info)
- `Update(msg)` handles messages and keyboard input
- `View()` renders the current state

**Styling:** Uses Charmbracelet's Lipgloss (`styles/` package)

**Entry point:** `main.go`

## Test Cluster Details

The Docker environment (`test-cluster/`) provides:
- 6 containers: mysql, slurmdbd, slurmctld, slurmrestd, node1, node2
- Test users: alice, bob, carol, dave
- Partitions: compute (default), gpu
- Fake jobs simulating ML training, data pipelines, genome alignment, matrix operations, and intentional failures

### Slurm REST API

slurmrestd setup requirements:
- **User**: Must run as dedicated `slurmrest` user (not root, not slurm)
- **Database**: Requires slurmdbd + MySQL (can't use `accounting_storage/none`)
- **Docker**: Needs `privileged: true` in docker-compose
- **JWT Auth**: Requires `AuthAltTypes=auth/jwt` and `AuthAltParameters=jwt_key=/etc/slurm/jwt.key` in **both** slurm.conf **and** slurmdbd.conf
- **JWT Key**: Must be binary (32 bytes from /dev/urandom), not hex string. Needs chmod 640 with slurm:slurmrest ownership so both daemons can read it
- **Privilege drop**: Use `gosu slurmrest` to run slurmrestd as non-root
- **slurmrestd startup**: Requires `SLURM_JWT=daemon` env var and `-a rest_auth/jwt` flag
- **API version**: Slurm 21.08 uses `/slurm/v0.0.37/` (not v0.0.42)

```bash
make rest-ping            # Test REST API ping (auto-fetches token)
make rest-jobs            # Get jobs via REST API (auto-fetches token)
make rest-token           # Generate JWT token manually
```

## Reference Implementation

The Python version in `stui-old-py/` shows the target feature set:
- `backend.py` - Slurm command execution
- `views/jobs.py` - Job list view with filtering
- `views/nodes.py` - Node status view
