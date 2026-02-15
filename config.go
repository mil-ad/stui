package main

import (
	"errors"
	"os"
	"path/filepath"

	"github.com/BurntSushi/toml"
)

type config struct {
	Backend string     `toml:"backend"` // "local" (default) or "rest"
	Rest    restConfig `toml:"rest"`
}

type restConfig struct {
	URL        string `toml:"url"`         // e.g. "http://localhost:6820"
	APIVersion string `toml:"api_version"` // default "v0.0.37"
	Username   string `toml:"username"`
	Token      string `toml:"token"`
}

func defaultConfig() config {
	return config{
		Backend: "local",
		Rest: restConfig{
			APIVersion: "v0.0.37",
		},
	}
}

// loadConfig reads the config from $XDG_CONFIG_HOME/stui/config.toml (or
// ~/.config/stui/config.toml). If the file doesn't exist, it returns
// defaultConfig. A malformed file is an error.
func loadConfig() (config, error) {
	path := configPath()

	cfg := defaultConfig()

	_, err := os.Stat(path)
	if errors.Is(err, os.ErrNotExist) {
		return cfg, nil
	}
	if err != nil {
		return cfg, err
	}

	if _, err := toml.DecodeFile(path, &cfg); err != nil {
		return cfg, err
	}

	// Apply defaults for fields not set in file
	if cfg.Rest.APIVersion == "" {
		cfg.Rest.APIVersion = "v0.0.37"
	}

	return cfg, nil
}

func configPath() string {
	dir := os.Getenv("XDG_CONFIG_HOME")
	if dir == "" {
		home, _ := os.UserHomeDir()
		dir = filepath.Join(home, ".config")
	}
	return filepath.Join(dir, "stui", "config.toml")
}
