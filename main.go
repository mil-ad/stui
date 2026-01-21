package main

import (
	"fmt"

	tea "charm.land/bubbletea/v2"
)

type clusterInfo string

func fetchInfo() tea.Msg {
	return clusterInfo("MyCluster")
}

type model struct {
	cluster_name string
	jobs         []string
	nodes        []string
}

func initialModel() model {
	m := model{
		cluster_name: "N/A",
		jobs:         []string{},
		nodes:        []string{},
	}

	return m
}

func (m model) Init() tea.Cmd {
	return fetchInfo
}

func (m model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case clusterInfo:
		m.cluster_name = string(msg)
	case tea.KeyMsg:
		switch msg.String() {
		case "q":
			return m, tea.Quit
		}
	}
	return m, nil
}

func (m model) View() tea.View {
	v := tea.NewView(fmt.Sprintf("cluster name:%s", m.cluster_name))

	v.AltScreen = true

	return v
}

func main() {
	p := tea.NewProgram(initialModel())

	p.Run()
	// TODO: add error handling
}
