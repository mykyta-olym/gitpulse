package build

import (
	_logger "gitlab.com/gitlab-org/technical-writing/docs-gitlab-com/cmd/internal/logger"
)

var logger *_logger.Logger

func init() {
	logger = _logger.NewDefault()
}
