package slurm

import (
	"fmt"
	"os/exec"
	"strconv"
	"strings"
	"time"
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
	out, err := exec.Command("squeue",
		"--noheader", "--all",
		"--format=%A|%j|%u|%a|%T|%P|%N|%D|%C|%l|%M|%V|%S|%e|%Q|%r|%o|%Z",
	).Output()
	if err != nil {
		return nil, fmt.Errorf("squeue: %w", err)
	}

	lines := strings.Split(strings.TrimSpace(string(out)), "\n")
	if len(lines) == 1 && lines[0] == "" {
		return nil, nil
	}

	jobs := make([]Job, 0, len(lines))
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		fields := strings.SplitN(line, "|", 18)
		if len(fields) < 18 {
			continue
		}

		// %A may return "100_3" for array jobs; take the base ID
		idStr, _, _ := strings.Cut(fields[0], "_")
		jobID := parseUint32(idStr)

		jobs = append(jobs, Job{
			JobID:     jobID,
			Name:      fields[1],
			User:      fields[2],
			Account:   fields[3],
			State:     JobState(fields[4]),
			Partition: fields[5],
			Nodes:     fields[6],
			NumNodes:  parseUint32(fields[7]),
			NumCPUs:   parseUint32(fields[8]),
			TimeLimit: parseSlurmDuration(fields[9]),
			RunTime:   parseSlurmDuration(fields[10]),
			Submit:    parseSlurmTimestamp(fields[11]),
			Start:     parseSlurmTimestamp(fields[12]),
			End:       parseSlurmTimestamp(fields[13]),
			Priority:  parseUint32(fields[14]),
			Reason:    fields[15],
			Command:   fields[16],
			WorkDir:   fields[17],
		})
	}

	return jobs, nil
}

func parseUint32(s string) uint32 {
	v, _ := strconv.ParseUint(strings.TrimSpace(s), 10, 32)
	return uint32(v)
}

// parseSlurmDuration handles MM:SS, HH:MM:SS, D-HH:MM:SS, UNLIMITED, INVALID, N/A.
func parseSlurmDuration(s string) time.Duration {
	s = strings.TrimSpace(s)
	switch s {
	case "UNLIMITED", "INVALID", "N/A", "":
		return 0
	}

	var days, hours, minutes, seconds int

	// Check for D-HH:MM:SS
	if dayPart, rest, ok := strings.Cut(s, "-"); ok {
		days, _ = strconv.Atoi(dayPart)
		s = rest
	}

	parts := strings.Split(s, ":")
	switch len(parts) {
	case 3: // HH:MM:SS
		hours, _ = strconv.Atoi(parts[0])
		minutes, _ = strconv.Atoi(parts[1])
		seconds, _ = strconv.Atoi(parts[2])
	case 2: // MM:SS
		minutes, _ = strconv.Atoi(parts[0])
		seconds, _ = strconv.Atoi(parts[1])
	}

	return time.Duration(days)*24*time.Hour +
		time.Duration(hours)*time.Hour +
		time.Duration(minutes)*time.Minute +
		time.Duration(seconds)*time.Second
}

// parseSlurmTimestamp parses "2006-01-02T15:04:05". Returns zero time for N/A/Unknown.
func parseSlurmTimestamp(s string) time.Time {
	s = strings.TrimSpace(s)
	switch s {
	case "N/A", "Unknown", "":
		return time.Time{}
	}
	t, _ := time.ParseInLocation("2006-01-02T15:04:05", s, time.Local)
	return t
}

func (c *LocalClient) FetchNodes() ([]Node, error) {
	return nil, nil
}
