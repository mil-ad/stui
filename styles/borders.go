package styles

import (
	"github.com/charmbracelet/lipgloss"
)

// TODO: this is probably not very useful because most of the methods mutate the same object
var BorderStyle = lipgloss.NewStyle().BorderStyle(lipgloss.RoundedBorder())
