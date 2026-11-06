// Runs GitLab's page-metadata generator for GitPulse navigation.
package main

import (
	"log"

	"gitlab.com/gitlab-org/technical-writing/docs-gitlab-com/cmd/internal/build"
)

func main() {
	if err := build.BuildPageMetadata(); err != nil {
		log.Fatalf("page metadata: %v", err)
	}
}
