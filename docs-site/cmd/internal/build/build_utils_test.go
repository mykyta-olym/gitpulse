package build

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/require"
)

type TestStruct struct {
	Name  string `yaml:"name"`
	Value int    `yaml:"value"`
}

func TestReadYAMLFile(t *testing.T) {
	// Create a temporary YAML file for testing
	content := []byte("name: test\nvalue: 42")
	tmpfile, err := os.CreateTemp(t.TempDir(), "test*.yaml")
	require.NoError(t, err)
	require.NoError(t, tmpfile.Close())

	err = os.WriteFile(tmpfile.Name(), content, 0600)
	require.NoError(t, err)

	// Test successful read
	var result TestStruct
	err = ReadYAMLFile(tmpfile.Name(), &result)
	require.NoError(t, err)
	require.Equal(t, "test", result.Name)
	require.Equal(t, 42, result.Value)

	// Test reading non-existent file
	err = ReadYAMLFile("nonexistent.yaml", &result)
	require.Error(t, err)

	// Test invalid YAML
	invalidContent := []byte("invalid: yaml: :")
	err = os.WriteFile(tmpfile.Name(), invalidContent, 0600)
	require.NoError(t, err)
	err = ReadYAMLFile(tmpfile.Name(), &result)
	require.Error(t, err)
}

func TestCreateDirectory(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := filepath.Join(t.TempDir(), "test_dir")

	// Test creating a new directory
	err := CreateDirectory(tmpDir)
	require.NoError(t, err)

	// Verify directory exists and has correct permissions
	info, err := os.Stat(tmpDir)
	require.NoError(t, err)
	require.True(t, info.IsDir())
	require.Equal(t, os.FileMode(0700), info.Mode().Perm())

	// Test creating an existing directory (should not error)
	err = CreateDirectory(tmpDir)
	require.NoError(t, err)

	// Test creating directory with invalid path
	err = CreateDirectory("/proc/invalid/path")
	require.Error(t, err)
}

func TestWriteBuildFile(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()

	// Test basic file writing
	filename := filepath.Join(tmpDir, "test.txt")
	content := []byte("test content")
	err := WriteBuildFile(filename, content)
	require.NoError(t, err)

	// Verify file contents and permissions
	readContent, err := os.ReadFile(filename)
	require.NoError(t, err)
	require.Equal(t, content, readContent)

	info, err := os.Stat(filename)
	require.NoError(t, err)
	require.Equal(t, os.FileMode(0444), info.Mode().Perm())

	// Test writing to an invalid path
	err = WriteBuildFile("/proc/invalid/path/file.txt", content)
	require.Error(t, err)
}

func TestBuildFileManager(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()

	// Resolve symlinks in tmpDir
	tmpDir, err := filepath.EvalSymlinks(tmpDir)
	require.NoError(t, err)

	// Change working directory to temp directory for testing
	t.Chdir(tmpDir)

	// Create a new DataFileManager instance
	fileManager := NewBuildFileManager("test.json")

	// Test that paths are set correctly
	require.Equal(t, "data", fileManager.DataDir)
	require.Equal(t, filepath.Join(tmpDir, "data", "test.json"), fileManager.OutputPath)

	// Test PrepareAndWrite
	testData := []byte("test content")
	err = fileManager.PrepareAndWrite(testData)
	require.NoError(t, err)

	// Verify file was created and contains correct content
	content, err := os.ReadFile(fileManager.OutputPath)
	require.NoError(t, err)
	require.Equal(t, testData, content)

	// Test overwriting existing file
	newData := []byte("new content")
	err = fileManager.PrepareAndWrite(newData)
	require.NoError(t, err)

	content, err = os.ReadFile(fileManager.OutputPath)
	require.NoError(t, err)
	require.Equal(t, newData, content)
}

func TestCleanupExistingFile(t *testing.T) {
	// Create a temporary directory for testing
	tmpDir := t.TempDir()

	// Test cleanup of existing file
	testFile := filepath.Join(tmpDir, "test.txt")
	err := os.WriteFile(testFile, []byte("test"), 0644)
	require.NoError(t, err)

	err = CleanupExistingFile(testFile)
	require.NoError(t, err)
	_, err = os.Stat(testFile)
	require.True(t, os.IsNotExist(err))

	// Test cleanup of non-existent file
	err = CleanupExistingFile(filepath.Join(tmpDir, "nonexistent.txt"))
	require.NoError(t, err)

	// Test cleanup with invalid path (use a null character, which is invalid in paths)
	err = CleanupExistingFile(string([]byte{0}))
	require.Error(t, err)
}
