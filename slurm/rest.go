package slurm

type RESTClient struct {
	BaseURL string
	Token   string
}

func NewRESTClient(baseURL, token string) *RESTClient {
	return &RESTClient{
		BaseURL: baseURL,
		Token:   token,
	}
}

func (c *RESTClient) FetchClusterInfo() (ClusterInfo, error) {
	return ClusterInfo{}, nil
}

func (c *RESTClient) FetchJobs() ([]Job, error) {
	return nil, nil
}

func (c *RESTClient) FetchNodes() ([]Node, error) {
	return nil, nil
}
