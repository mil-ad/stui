package main

import (
	"fmt"

	"github.com/mil-ad/stui/slurm"
	"github.com/mil-ad/stui/styles"

	tea "github.com/charmbracelet/bubbletea"
)

// Messages

type clusterConnectedMsg struct {
	client  slurm.Client
	cluster slurm.ClusterInfo
}

type clusterErrorMsg struct {
	err error
}

// Commands

func discoverCluster() tea.Msg {
	c := slurm.NewLocalClient()

	if err := c.Probe(); err != nil {
		return clusterErrorMsg{err: fmt.Errorf("local slurm not available: %w", err)}
	}

	info, err := c.FetchClusterInfo()
	if err != nil {
		return clusterErrorMsg{err: fmt.Errorf("failed to fetch cluster info: %w", err)}
	}

	return clusterConnectedMsg{client: c, cluster: info}
}

// Model

type model struct {
	client     slurm.Client
	cluster    slurm.ClusterInfo
	connecting bool
	err        error

	jobs  []slurm.Job
	nodes []slurm.Node

	height int
	width  int
}

func initialModel() model {
	return model{
		connecting: true,
		jobs:       []slurm.Job{},
		nodes:      []slurm.Node{},
	}
}

func (m model) Init() tea.Cmd {
	return discoverCluster
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case clusterConnectedMsg:
		m.client = msg.client
		m.cluster = msg.cluster
		m.connecting = false
	case clusterErrorMsg:
		m.err = msg.err
		m.connecting = false
	case tea.KeyMsg:
		switch msg.String() {
		case "q":
			return m, tea.Quit
		}
	case tea.WindowSizeMsg:
		m.height = msg.Height
		m.width = msg.Width
	}
	return m, nil
}

func (m model) View() string {
	var content string

	switch {
	case m.connecting:
		content = "Connecting..."
	case m.err != nil:
		content = fmt.Sprintf("Error: %v", m.err)
	default:
		content = fmt.Sprintf("cluster: %s  version: %s", m.cluster.Name, m.cluster.Version)
	}

	return styles.BorderStyle.
		Width(m.width - 2).
		Height(m.height - 2).
		Render(content)
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())

	p.Run()
	// TODO: add error handling
}
