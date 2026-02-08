package slurm

type NodeState string

const (
	NodeIdle      NodeState = "IDLE"
	NodeAllocated NodeState = "ALLOCATED"
	NodeMixed     NodeState = "MIXED"
	NodeDown      NodeState = "DOWN"
	NodeDrained   NodeState = "DRAINED"
	NodeDraining  NodeState = "DRAINING"
	NodeUnknown   NodeState = "UNKNOWN"
)

type Node struct {
	Name      string
	State     NodeState
	Partition string
	CPUs      uint32
	AllocCPUs uint32
	Memory    uint64 // total memory in MB
	AllocMem  uint64 // allocated memory in MB
	FreeMem   uint64 // free memory in MB
	CPULoad   float64
	Sockets   uint32
	Cores     uint32 // cores per socket
	Threads   uint32 // threads per core
	Features  string
	Gres      string // generic resources (e.g. GPUs)
	Reason    string // reason for DOWN/DRAINED state
	Weight    uint32
}
