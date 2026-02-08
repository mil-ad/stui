package slurm

type ClusterInfo struct {
	Name    string
	Version string
}

type Client interface {
	FetchClusterInfo() (ClusterInfo, error)
	FetchJobs() ([]Job, error)
	FetchNodes() ([]Node, error)
}
