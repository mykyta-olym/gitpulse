package build

import (
	"fmt"
	"os"
	"path/filepath"

	"go.yaml.in/yaml/v3"
)

// NavItem represents a navigation item in the navigation.yaml structure
type NavItem struct {
	Title   string    `yaml:"title"`
	URL     string    `yaml:"url"`
	Submenu []NavItem `yaml:"submenu,omitempty"`
}

// Read and parse a YAML file into the provided interface
func ReadYAMLFile(filename string, out interface{}) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("error reading YAML file %s: %w", filename, err)
	}

	if err := yaml.Unmarshal(data, out); err != nil {
		return fmt.Errorf("error parsing YAML from %s: %w", filename, err)
	}

	return nil
}

type BuildFileManager struct {
	OutputPath string
	DataDir    string
}

func NewBuildFileManager(filename string) *BuildFileManager {
	dir, _ := os.Getwd()
	return &BuildFileManager{
		OutputPath: filepath.Join(dir, "data", filename),
		DataDir:    "data",
	}
}

func (dm *BuildFileManager) PrepareAndWrite(data []byte) error {
	// Clean up existing file
	if err := CleanupExistingFile(dm.OutputPath); err != nil {
		return err
	}

	// Ensure directory exists
	if err := CreateDirectory(dm.DataDir); err != nil {
		return err
	}

	// Write the file
	if err := WriteBuildFile(dm.OutputPath, data); err != nil {
		return err
	}

	return nil
}

// Creates a directory if it doesn't exist
func CreateDirectory(dir string) error {
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("error creating directory %s: %w", dir, err)
	}
	return nil
}

// Removes a file if it already exists
func CleanupExistingFile(filepath string) error {
	if err := os.Remove(filepath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("error removing existing file %s: %w", filepath, err)
	}
	return nil
}

// Write a file that we've created in the build stage
func WriteBuildFile(filename string, data []byte) error {
	if err := os.WriteFile(filename, data, 0444); err != nil {
		return fmt.Errorf("error writing file %s: %w", filename, err)
	}
	return nil
}
