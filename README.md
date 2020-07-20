[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Follow @notmilad](https://img.shields.io/twitter/follow/notmilad?style=social)](https://twitter.com/notmilad)

# stui
A Slurm dashboard for the terminal.

<img src="screenshot.png" alt="stui screenshot" width="75%"/>

## Features
* Connect to local Slurm cluster or remote clusters via SSH
* Quickly filter jobs based on commonly-used criteria
* Cancel, attach to, or modify properties of selected jobs.

## Installation

```shell
$ pip install stui
```

## Usage

On a machine that's part of a Slurm cluster simply fire up `stui`:

```shell
$ stui
```

To connect to a remote Slurm cluster via SSH:

```shell
$ stui --remote REMOTE_MACHINE
```

`REMOTE_MACHINE` format is `USER@SERVER_ADDR` or simply the `Host` name specified in the SSH config file.

N.B. there's currently no support for authenticating SSH connections with passwords. SSH keys must have been exchanged for the remote functionality to work.
