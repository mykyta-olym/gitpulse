package logger

import (
	"io"
	"os"
	"strings"
	"time"

	"charm.land/lipgloss/v2"
	"charm.land/log/v2"
)

type Logger struct {
	*log.Logger
}

func NewDefault() *Logger {
	return New(os.Stderr)
}

func New(w io.Writer) *Logger {
	styles := log.DefaultStyles()
	// See also makefiles/Makefile.common.mk and scripts/scripts-common.sh
	styles.Levels[log.DebugLevel] = lipgloss.NewStyle().
		SetString(strings.ToUpper(log.DebugLevel.String())).
		Bold(true).
		MaxWidth(5).
		// Default (https://github.com/charmbracelet/log/blob/v2.0.0/styles.go)
		Foreground(lipgloss.Color("63"))
	styles.Levels[log.InfoLevel] = lipgloss.NewStyle().
		SetString(strings.ToUpper(log.InfoLevel.String())).
		Bold(true).
		MaxWidth(5).
		// Standard green (https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit)
		Foreground(lipgloss.Color("2"))
	styles.Levels[log.WarnLevel] = lipgloss.NewStyle().
		SetString(strings.ToUpper(log.WarnLevel.String())).
		Bold(true).
		MaxWidth(5).
		// Standard yellow (https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit)
		Foreground(lipgloss.Color("3"))
	styles.Levels[log.ErrorLevel] = lipgloss.NewStyle().
		SetString(strings.ToUpper(log.ErrorLevel.String())).
		Bold(true).
		MaxWidth(5).
		// Standard red (https://en.wikipedia.org/wiki/ANSI_escape_code#8-bit)
		Foreground(lipgloss.Color("1"))
	styles.Levels[log.FatalLevel] = lipgloss.NewStyle().
		SetString(strings.ToUpper(log.FatalLevel.String())).
		Bold(true).
		MaxWidth(5).
		// Default (https://github.com/charmbracelet/log/blob/v2.0.0/styles.go)
		Foreground(lipgloss.Color("134"))

	l := log.New(w)
	l.SetStyles(styles)
	l.SetReportTimestamp(true)
	l.SetTimeFormat(time.DateTime)

	return &Logger{l}
}
