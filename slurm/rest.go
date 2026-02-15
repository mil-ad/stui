package slurm

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type RESTClient struct {
	baseURL    string
	apiVersion string
	username   string
	token      string
	http       *http.Client
}

func NewRESTClient(baseURL, apiVersion, username, token string) *RESTClient {
	return &RESTClient{
		baseURL:    strings.TrimRight(baseURL, "/"),
		apiVersion: apiVersion,
		username:   username,
		token:      token,
		http:       &http.Client{Timeout: 10 * time.Second},
	}
}

func (c *RESTClient) doGet(endpoint string, target any) error {
	url := fmt.Sprintf("%s/slurm/%s/%s", c.baseURL, c.apiVersion, endpoint)

	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("X-SLURM-USER-NAME", c.username)
	req.Header.Set("X-SLURM-USER-TOKEN", c.token)

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("REST API returned %s", resp.Status)
	}

	return json.NewDecoder(resp.Body).Decode(target)
}

// Probe checks whether the REST API is reachable and a controller is UP.
func (c *RESTClient) Probe() error {
	var resp restPingResponse
	if err := c.doGet("ping", &resp); err != nil {
		return fmt.Errorf("REST API ping failed: %w", err)
	}

	for _, ctl := range resp.Pings {
		if strings.EqualFold(ctl.Ping, "UP") {
			return nil
		}
	}
	return fmt.Errorf("no Slurm controller is UP")
}

func (c *RESTClient) FetchClusterInfo() (ClusterInfo, error) {
	var resp restPingResponse
	if err := c.doGet("ping", &resp); err != nil {
		return ClusterInfo{}, fmt.Errorf("REST API ping: %w", err)
	}

	info := ClusterInfo{
		Version: resp.Meta.Slurm.Release,
	}

	for _, ctl := range resp.Pings {
		if strings.EqualFold(ctl.Ping, "UP") {
			info.Name = ctl.Hostname
			break
		}
	}

	return info, nil
}

func (c *RESTClient) FetchJobs() ([]Job, error) {
	var resp restJobsResponse
	if err := c.doGet("jobs", &resp); err != nil {
		return nil, fmt.Errorf("REST API jobs: %w", err)
	}

	now := time.Now()
	jobs := make([]Job, 0, len(resp.Jobs))
	for _, rj := range resp.Jobs {
		start := unixToTime(rj.StartTime)
		end := unixToTime(rj.EndTime)

		var runTime time.Duration
		state := JobState(strings.ToUpper(rj.JobState))
		switch state {
		case JobRunning:
			if !start.IsZero() {
				runTime = now.Sub(start)
			}
		default:
			if !start.IsZero() && !end.IsZero() {
				runTime = end.Sub(start)
			}
		}

		jobs = append(jobs, Job{
			JobID:     rj.JobID,
			Name:      rj.Name,
			User:      rj.UserName,
			Account:   rj.Account,
			State:     state,
			Partition: rj.Partition,
			Nodes:     rj.Nodes,
			NumNodes:  rj.NodeCount,
			NumCPUs:   rj.CPUs,
			TimeLimit: time.Duration(rj.TimeLimit) * time.Minute,
			RunTime:   runTime,
			Submit:    unixToTime(rj.SubmitTime),
			Start:     start,
			End:       end,
			Priority:  rj.Priority,
			Reason:    rj.StateReason,
			Command:   rj.Command,
			WorkDir:   rj.CurrentWorkingDirectory,
		})
	}

	return jobs, nil
}

func (c *RESTClient) FetchNodes() ([]Node, error) {
	var resp restNodesResponse
	if err := c.doGet("nodes", &resp); err != nil {
		return nil, fmt.Errorf("REST API nodes: %w", err)
	}

	nodes := make([]Node, 0, len(resp.Nodes))
	for _, rn := range resp.Nodes {
		nodes = append(nodes, Node{
			Name:      rn.Name,
			State:     NodeState(strings.ToUpper(rn.State)),
			Partition: strings.Join(rn.Partitions, ","),
			CPUs:      rn.CPUs,
			AllocCPUs: rn.AllocCPUs,
			Memory:    rn.RealMemory,
			AllocMem:  rn.AllocMemory,
			FreeMem:   rn.FreeMemory,
			CPULoad:   float64(rn.CPULoad) / 100.0,
			Sockets:   rn.Sockets,
			Cores:     rn.CoresPerSocket,
			Threads:   rn.ThreadsPerCore,
			Features:  rn.Features,
			Gres:      rn.Gres,
			Reason:    rn.Reason,
			Weight:    rn.Weight,
		})
	}

	return nodes, nil
}

func unixToTime(epoch int64) time.Time {
	if epoch == 0 {
		return time.Time{}
	}
	return time.Unix(epoch, 0)
}

// JSON response types matching Slurm REST API v0.0.37

type restPingResponse struct {
	Meta  restMeta   `json:"meta"`
	Pings []restPing `json:"pings"`
}

type restMeta struct {
	Slurm restSlurmMeta `json:"Slurm"`
}

type restSlurmMeta struct {
	Release string `json:"release"`
}

type restPing struct {
	Hostname string `json:"hostname"`
	Ping     string `json:"ping"`
	Mode     string `json:"mode"`
}

type restJobsResponse struct {
	Jobs []restJob `json:"jobs"`
}

type restJob struct {
	JobID                   uint32 `json:"job_id"`
	Name                    string `json:"name"`
	UserName                string `json:"user_name"`
	Account                 string `json:"account"`
	JobState                string `json:"job_state"`
	Partition               string `json:"partition"`
	Nodes                   string `json:"nodes"`
	NodeCount               uint32 `json:"node_count"`
	CPUs                    uint32 `json:"cpus"`
	TimeLimit               uint32 `json:"time_limit"`
	SubmitTime              int64  `json:"submit_time"`
	StartTime               int64  `json:"start_time"`
	EndTime                 int64  `json:"end_time"`
	Priority                uint32 `json:"priority"`
	StateReason             string `json:"state_reason"`
	Command                 string `json:"command"`
	CurrentWorkingDirectory string `json:"current_working_directory"`
}

type restNodesResponse struct {
	Nodes []restNode `json:"nodes"`
}

type restNode struct {
	Name           string   `json:"name"`
	State          string   `json:"state"`
	Partitions     []string `json:"partitions"`
	CPUs           uint32   `json:"cpus"`
	AllocCPUs      uint32   `json:"alloc_cpus"`
	RealMemory     uint64   `json:"real_memory"`
	AllocMemory    uint64   `json:"alloc_memory"`
	FreeMemory     uint64   `json:"free_memory"`
	CPULoad        int64    `json:"cpu_load"`
	Sockets        uint32   `json:"sockets"`
	CoresPerSocket uint32   `json:"cores_per_socket"`
	ThreadsPerCore uint32   `json:"threads_per_core"`
	Features       string   `json:"features"`
	Gres           string   `json:"gres"`
	Reason         string   `json:"reason"`
	Weight         uint32   `json:"weight"`
}
