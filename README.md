# stui

A terminal dashboard for Slurm clusters.

## Install

Download a binary from [Releases](https://github.com/mi-lad/slurmtui/releases), or build from source:

```
go build -o stui
```

## Usage

```
stui            # uses local Slurm commands
stui --version  # print version
```

To connect via the Slurm REST API, create `~/.config/stui/config.toml`:

```toml
backend = "rest"

[rest]
url = "http://cluster.example.com:6820"
username = "alice"
token = "your-jwt-token"
```

See `man stui(5)` for all configuration options.

## License

MIT
