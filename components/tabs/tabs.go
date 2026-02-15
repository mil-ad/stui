package tabs

import (
	"strings"

	"github.com/charmbracelet/bubbles/key"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

type KeyMap struct {
	NextTab key.Binding
	PrevTab key.Binding
}

var DefaultKeyMap = KeyMap{
	NextTab: key.NewBinding(
		key.WithKeys("tab"),
		key.WithHelp("tab", "next tab"),
	),
	PrevTab: key.NewBinding(
		key.WithKeys("shift+tab"),
		key.WithHelp("shift+tab", "prev tab"),
	),
}

type Model struct {
	Tabs      []string
	ActiveTab int
	KeyMap    KeyMap

	width   int
	height  int
	content string
}

func New(tabs ...string) Model {
	return Model{
		Tabs:   tabs,
		KeyMap: DefaultKeyMap,
	}
}

func (m *Model) SetContent(s string) {
	m.content = s
}

func (m *Model) SetWidth(w int) {
	m.width = w
}

func (m *Model) SetHeight(h int) {
	m.height = h
}

func (m Model) Update(msg tea.Msg) (Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch {
		case key.Matches(msg, m.KeyMap.NextTab):
			m.ActiveTab = (m.ActiveTab + 1) % len(m.Tabs)
		case key.Matches(msg, m.KeyMap.PrevTab):
			m.ActiveTab = (m.ActiveTab - 1 + len(m.Tabs)) % len(m.Tabs)
		}
	}
	return m, nil
}

func tabBorderWithBottom(left, middle, right string) lipgloss.Border {
	border := lipgloss.RoundedBorder()
	border.BottomLeft = left
	border.Bottom = middle
	border.BottomRight = right
	return border
}

var (
	borderColor = lipgloss.Color("240")

	activeTabBorder   = tabBorderWithBottom("┘", " ", "└")
	inactiveTabBorder = tabBorderWithBottom("─", "─", "─")

	activeTabStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("86")).
			Padding(0, 2).
			Border(activeTabBorder, true).
			BorderForeground(lipgloss.Color("86"))

	inactiveTabStyle = lipgloss.NewStyle().
				Padding(0, 2).
				Border(inactiveTabBorder, true).
				BorderForeground(lipgloss.Color("86"))
)

func (m Model) View() string {
	var renderedTabs []string

	for i, t := range m.Tabs {
		isFirst, isActive := i == 0, i == m.ActiveTab

		var style lipgloss.Style
		if isActive {
			style = activeTabStyle
		} else {
			style = inactiveTabStyle
		}

		border, _, _, _, _ := style.GetBorder()
		if isFirst && isActive {
			border.BottomLeft = "│"
		} else if isFirst {
			border.BottomLeft = "╭"
		}
		style = style.Border(border)
		renderedTabs = append(renderedTabs, style.Render(t))
	}

	row := lipgloss.JoinHorizontal(lipgloss.Top, renderedTabs...)

	// Fill gap between last tab and window right edge
	gapWidth := m.width - lipgloss.Width(row)
	if gapWidth > 0 {
		gapLine := lipgloss.NewStyle().
			Foreground(activeTabStyle.GetBorderTopForeground()).
			Render(strings.Repeat("─", gapWidth-1) + "╮")
		row = lipgloss.JoinHorizontal(lipgloss.Bottom, row, gapLine)
	}

	// Content window — no top border, tabs serve as the top edge
	contentWidth := m.width - 2
	if contentWidth < 0 {
		contentWidth = 0
	}
	contentHeight := m.height - lipgloss.Height(row) - 1
	if contentHeight < 0 {
		contentHeight = 0
	}

	highlightColor := activeTabStyle.GetBorderTopForeground()

	windowStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderTop(false).
		BorderForeground(highlightColor).
		Width(contentWidth).
		Height(contentHeight)

	window := windowStyle.Render(m.content)

	return lipgloss.JoinVertical(lipgloss.Left, row, window)
}
