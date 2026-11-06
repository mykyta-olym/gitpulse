package logger

import (
	"bytes"
	"io"
	"testing"

	"charm.land/log/v2"
	"github.com/charmbracelet/x/ansi"
	"github.com/stretchr/testify/require"
)

func TestNew(t *testing.T) {
	testStr := "test output"

	testCases := []struct {
		name     string
		level    log.Level
		expected string
	}{
		{
			name:     "info",
			level:    log.InfoLevel,
			expected: "INFO " + testStr,
		},
		{
			name:     "error",
			level:    log.ErrorLevel,
			expected: "ERROR " + testStr,
		},
	}

	b := &bytes.Buffer{}
	logger := New(b)
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			logger.Log(tc.level, testStr)

			actual, err := io.ReadAll(b)
			require.NoError(t, err)

			require.Contains(t, ansi.Strip(string(actual)), tc.expected)
		})
	}
}
