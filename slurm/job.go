package slurm

import "time"

type JobState string

const (
	JobPending   JobState = "PENDING"
	JobRunning   JobState = "RUNNING"
	JobSuspended JobState = "SUSPENDED"
	JobCompleted JobState = "COMPLETED"
	JobCancelled JobState = "CANCELLED"
	JobFailed    JobState = "FAILED"
	JobTimeout   JobState = "TIMEOUT"
	JobNodeFail  JobState = "NODE_FAIL"
	JobPreempted JobState = "PREEMPTED"
)

type Job struct {
	JobID     uint32
	Name      string
	User      string
	Account   string
	State     JobState
	Partition string
	Nodes     string // allocated node list
	NumNodes  uint32
	NumCPUs   uint32
	TimeLimit time.Duration
	RunTime   time.Duration
	Submit    time.Time
	Start     time.Time
	End       time.Time
	Priority  uint32
	Reason    string // reason pending, or nodelist if running
	Command   string
	WorkDir   string
}
