package slurm

import (
	"fmt"
	"os/exec"
	"strings"
)

type LocalClient struct{}

func NewLocalClient() *LocalClient {
	return &LocalClient{}
}

// Probe checks whether Slurm CLI tools are available locally.
func (c *LocalClient) Probe() error {
	return exec.Command("sinfo", "--version").Run()
}

func (c *LocalClient) FetchClusterInfo() (ClusterInfo, error) {
	out, err := exec.Command("scontrol", "show", "config").Output()
	if err != nil {
		return ClusterInfo{}, fmt.Errorf("scontrol show config: %w", err)
	}

	config := parseScontrolConfig(string(out))

	return ClusterInfo{
		Name:    config["ClusterName"],
		Version: config["SLURM_VERSION"],
	}, nil
}

// parseScontrolConfig parses the "Key = Value" lines from scontrol show config.
func parseScontrolConfig(output string) map[string]string {
	config := make(map[string]string)
	for _, line := range strings.Split(output, "\n") {
		key, value, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		config[strings.TrimSpace(key)] = strings.TrimSpace(value)
	}
	return config
}

func (c *LocalClient) FetchJobs() ([]Job, error) {
	return nil, nil
}

func (c *LocalClient) FetchNodes() ([]Node, error) {
	return nil, nil
}
