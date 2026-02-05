package main

import (
	"fmt"

	"github.com/mil-ad/stui/styles"

	tea "github.com/charmbracelet/bubbletea"
)

type clusterInfoMsg string

func fetchInfo() tea.Msg {
	return clusterInfoMsg("MyCluster")
}

type model struct {
	cluster_name string
	jobs         []Job
	nodes        []Node

	height int
	width  int
}

func initialModel() model {
	m := model{
		cluster_name: "N/A",
		jobs:         []Job{},
		nodes:        []Node{},
	}

	return m
}

func (m model) Init() tea.Cmd {
	return fetchInfo
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case clusterInfoMsg:
		m.cluster_name = string(msg)
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
	return styles.BorderStyle.
		Width(m.width - 2).
		Height(m.height - 2).
		Render(fmt.Sprintf("cluster name:%s", m.cluster_name))
}

func main() {
	p := tea.NewProgram(initialModel(), tea.WithAltScreen())

	p.Run()
	// TODO: add error handling
}
