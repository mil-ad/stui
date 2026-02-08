package slurm

import "os/exec"

type LocalClient struct{}

func NewLocalClient() *LocalClient {
	return &LocalClient{}
}

// Probe checks whether Slurm CLI tools are available locally.
func (c *LocalClient) Probe() error {
	return exec.Command("sinfo", "--version").Run()
}

func (c *LocalClient) FetchClusterInfo() (ClusterInfo, error) {
	return ClusterInfo{}, nil
}

func (c *LocalClient) FetchJobs() ([]Job, error) {
	return nil, nil
}

func (c *LocalClient) FetchNodes() ([]Node, error) {
	return nil, nil
}
