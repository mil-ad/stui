package main

import (
	"fmt"
	"time"

	"github.com/charmbracelet/bubbles/help"
	"github.com/charmbracelet/bubbles/key"
	"github.com/charmbracelet/bubbles/table"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/mil-ad/stui/components/tabs"
	"github.com/mil-ad/stui/slurm"
	"github.com/mil-ad/stui/styles"
)

// Messages

type clusterConnectedMsg struct {
	client  slurm.Client
	cluster slurm.ClusterInfo
}

type clusterErrorMsg struct {
	err error
}

type jobsFetchedMsg struct {
	jobs []slurm.Job
}

type jobsFetchErrorMsg struct {
	err error
}

type tickMsg time.Time

// Commands

func discoverCluster() tea.Msg {

	// TODO: Don't assume Local. Make other clients work too.
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

func fetchJobs(client slurm.Client) tea.Cmd {
	return func() tea.Msg {
		jobs, err := client.FetchJobs()
		if err != nil {
			return jobsFetchErrorMsg{err: err}
		}
		return jobsFetchedMsg{jobs: jobs}
	}
}

func tickCmd() tea.Cmd {
	return tea.Tick(5*time.Second, func(t time.Time) tea.Msg {
		return tickMsg(t)
	})
}

// Key bindings

type keyMap struct {
	NextTab     key.Binding
	PrevTab     key.Binding
	Search      key.Binding
	Keybindings key.Binding
	Quit        key.Binding
}

func (k keyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.NextTab, k.PrevTab, k.Search, k.Keybindings, k.Quit}
}

func (k keyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{{k.NextTab, k.PrevTab, k.Search, k.Keybindings, k.Quit}}
}

var keys = keyMap{
	NextTab: key.NewBinding(
		key.WithKeys("tab"),
		key.WithHelp("tab", "next tab"),
	),
	PrevTab: key.NewBinding(
		key.WithKeys("shift+tab"),
		key.WithHelp("shift+tab", "prev tab"),
	),
	Search: key.NewBinding(
		key.WithKeys("/"),
		key.WithHelp("/", "search"),
	),
	Keybindings: key.NewBinding(
		key.WithKeys("?"),
		key.WithHelp("?", "keybindings"),
	),
	Quit: key.NewBinding(
		key.WithKeys("q"),
		key.WithHelp("q", "quit"),
	),
}

func newHelp() help.Model {
	keyStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color("86"))

	descStyle := lipgloss.NewStyle().
		Foreground(lipgloss.AdaptiveColor{Light: "#B2B2B2", Dark: "#626262"})

	sepStyle := lipgloss.NewStyle().
		Foreground(lipgloss.AdaptiveColor{Light: "#DDDADA", Dark: "#3C3C3C"})

	h := help.New()
	h.Styles = help.Styles{
		ShortKey:       keyStyle,
		ShortDesc:      descStyle,
		ShortSeparator: sepStyle,
		Ellipsis:       sepStyle,
		FullKey:        keyStyle,
		FullDesc:       descStyle,
		FullSeparator:  sepStyle,
	}
	return h
}

// Model

var tableColumns = []table.Column{
	{Title: "Job ID", Width: 8},
	{Title: "Name", Width: 20},
	{Title: "User", Width: 10},
	{Title: "State", Width: 12},
	{Title: "Partition", Width: 10},
	{Title: "Nodes", Width: 12},
	{Title: "CPUs", Width: 5},
	{Title: "Time", Width: 12},
	{Title: "Reason", Width: 16},
}

func newJobTable() table.Model {
	t := table.New(
		table.WithColumns(tableColumns),
		table.WithRows([]table.Row{}),
		table.WithFocused(true),
	)

	s := table.DefaultStyles()
	s.Header = s.Header.
		Bold(true).
		BorderStyle(lipgloss.NormalBorder()).
		BorderBottom(true).
		BorderForeground(lipgloss.Color("240"))
	s.Selected = s.Selected.
		Foreground(lipgloss.Color("229")).
		Background(lipgloss.Color("86"))
	t.SetStyles(s)

	return t
}

type model struct {
	client     slurm.Client
	cluster    slurm.ClusterInfo
	connecting bool
	err        error

	jobs     []slurm.Job
	jobTable table.Model
	tabs     tabs.Model

	keys keyMap
	help help.Model

	height int
	width  int
}

func newModel() model {
	return model{
		connecting: true,
		jobs:       []slurm.Job{},
		jobTable:   newJobTable(),
		tabs:       tabs.New("Jobs", "Nodes", "Admin"),
		keys:       keys,
		help:       newHelp(),
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
		return m, tea.Batch(fetchJobs(m.client), tickCmd())

	case jobsFetchedMsg:
		// Preserve selected job across refresh
		var selectedJobID string
		if sel := m.jobTable.SelectedRow(); sel != nil {
			selectedJobID = sel[0]
		}

		m.jobs = msg.jobs
		rows := jobsToRows(msg.jobs)
		m.jobTable.SetRows(rows)

		if selectedJobID != "" {
			for i, row := range rows {
				if row[0] == selectedJobID {
					m.jobTable.SetCursor(i)
					break
				}
			}
		}
		return m, nil

	case jobsFetchErrorMsg:
		m.err = msg.err
		return m, nil

	case tickMsg:
		if m.client != nil {
			return m, tea.Batch(fetchJobs(m.client), tickCmd())
		}
		return m, tickCmd()

	case tea.KeyMsg:
		switch {
		case key.Matches(msg, m.keys.Quit):
			return m, tea.Quit
		case key.Matches(msg, m.keys.NextTab), key.Matches(msg, m.keys.PrevTab):
			m.tabs, _ = m.tabs.Update(msg)
			return m, nil
		}

	case tea.WindowSizeMsg:
		m.height = msg.Height
		m.width = msg.Width
		m.help.Width = m.width
		// Tabs get full width; height excludes header line and help bar line
		m.tabs.SetWidth(m.width)
		m.tabs.SetHeight(m.height - 2) // header + help bar
		// Table sizes: content area is tabs height minus tab bar (2 lines) minus bottom border (1 line)
		// and width minus left+right borders (2 cols)
		m.jobTable.SetHeight(m.height - 2 - 3 - 2)
		m.jobTable.SetWidth(m.width - 4)
	}

	var cmd tea.Cmd
	m.jobTable, cmd = m.jobTable.Update(msg)
	return m, cmd
}

func (m model) View() string {
	switch {
	case m.connecting:
		return styles.BorderStyle.
			Width(m.width - 2).
			Height(m.height - 2).
			Render("Connecting...")
	case m.err != nil:
		return styles.BorderStyle.
			Width(m.width - 2).
			Height(m.height - 2).
			Render(fmt.Sprintf("Error: %v", m.err))
	}

	header := fmt.Sprintf(" %s (Slurm %s) — %d jobs", m.cluster.Name, m.cluster.Version, len(m.jobs))

	switch m.tabs.ActiveTab {
	case 0:
		m.tabs.SetContent(m.jobTable.View())
	case 1:
		m.tabs.SetContent("  Nodes view coming soon...")
	case 2:
		m.tabs.SetContent("  Admin view coming soon...")
	}

	helpView := m.help.View(m.keys)

	return header + "\n" + m.tabs.View() + "\n" + helpView
}

func jobsToRows(jobs []slurm.Job) []table.Row {
	rows := make([]table.Row, len(jobs))
	for i, j := range jobs {
		rows[i] = table.Row{
			fmt.Sprintf("%d", j.JobID),
			j.Name,
			j.User,
			string(j.State),
			j.Partition,
			j.Nodes,
			fmt.Sprintf("%d", j.NumCPUs),
			formatDuration(j.RunTime),
			j.Reason,
		}
	}
	return rows
}

func formatDuration(d time.Duration) string {
	if d == 0 {
		return "0:00"
	}
	total := int(d.Seconds())
	days := total / 86400
	hours := (total % 86400) / 3600
	minutes := (total % 3600) / 60
	seconds := total % 60

	if days > 0 {
		return fmt.Sprintf("%d-%02d:%02d:%02d", days, hours, minutes, seconds)
	}
	return fmt.Sprintf("%d:%02d:%02d", hours, minutes, seconds)
}

func main() {
	p := tea.NewProgram(newModel(), tea.WithAltScreen())

	p.Run()
	// TODO: add error handling
}
