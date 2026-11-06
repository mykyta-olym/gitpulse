package build

import (
	"encoding/json"
	"fmt"
	"maps"
	"path/filepath"
	"strings"

	"github.com/gosimple/slug"
)

// The language that owns the un-prefixed paths. Must match
// `defaultContentLanguage` in config/_default/hugo.yaml - the breadcrumb and the
// sidebar both assume the stored paths and the published URLs agree.
// Pinned by tests/unit/test_docs_default_language.py.
const langDefault = "sk"

type TrailItem struct {
	Title string `json:"title"`
	Path  string `json:"path"`
}

type Metatags struct {
	Section     string `json:"section"`
	TrailString string `json:"trail_string"`
}

type PageMetadata struct {
	Metatags   Metatags    `json:"metatags"`
	TrailItems []TrailItem `json:"trail_items"`
}

func BuildPageMetadata() error {
	// Get list of language directories
	languages, err := getLanguages()
	if err != nil {
		return fmt.Errorf("error getting languages: %w", err)
	}

	// Load English navigation to get section mappings
	sectionMap, err := buildSectionMap()
	if err != nil {
		return fmt.Errorf("error building section map: %w", err)
	}

	for _, lang := range languages {
		if err := buildMetadataForLanguage(lang, sectionMap); err != nil {
			return fmt.Errorf("error building metadata for language %s: %w", lang, err)
		}
	}

	logger.Info("All page metadata files created successfully.")
	return nil
}

func buildSectionMap() (map[string]string, error) {
	// Read English navigation to get section names
	var navigation []NavItem
	if err := ReadYAMLFile(fmt.Sprintf("data/%s/navigation.yaml", langDefault), &navigation); err != nil {
		return nil, fmt.Errorf("error reading English navigation YAML: %w", err)
	}

	sectionMap := make(map[string]string)
	for _, item := range navigation {
		section := makeSection(item.Title)
		// Map all paths under this top-level item to this section
		mapPathsToSection([]NavItem{item}, section, sectionMap)
	}

	return sectionMap, nil
}

func mapPathsToSection(items []NavItem, section string, sectionMap map[string]string) {
	for _, item := range items {
		sectionMap[item.URL] = section
		if len(item.Submenu) > 0 {
			mapPathsToSection(item.Submenu, section, sectionMap)
		}
	}
}

func buildMetadataForLanguage(lang string, sectionMap map[string]string) error {
	// Create language-specific output filename in data directory
	outputFileName := fmt.Sprintf("%s/page-metadata.json", lang)
	fileManager := NewBuildFileManager(outputFileName)

	// Read navigation data for this language
	navFilePath := fmt.Sprintf("data/%s/navigation.yaml", lang)
	var navigation []NavItem
	if err := ReadYAMLFile(navFilePath, &navigation); err != nil {
		return fmt.Errorf("error reading navigation YAML for %s: %w", lang, err)
	}

	// Process navigation to build page metadata (returns map directly)
	metadataMap := processNavigationForMetadata(navigation, []TrailItem{}, sectionMap, lang)

	// Marshal to JSON
	jsonData, err := json.MarshalIndent(metadataMap, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshaling JSON for %s: %w", lang, err)
	}

	// Write the file
	if err := fileManager.PrepareAndWrite(jsonData); err != nil {
		return fmt.Errorf("error writing metadata file for %s: %w", lang, err)
	}

	logger.Infof("data/%s/page-metadata.json file created successfully.", lang)
	return nil
}

func processNavigationForMetadata(items []NavItem, parentTrail []TrailItem, sectionMap map[string]string, lang string) map[string]PageMetadata {
	metadata := make(map[string]PageMetadata)
	isTopLevel := len(parentTrail) == 0

	for _, item := range items {
		// Add the langcode prefix for non-English paths
		path := item.URL
		if lang != langDefault {
			path = fmt.Sprintf("%s/%s", lang, item.URL)
		}

		// Create a copy to avoid slice aliasing issues
		currentTrail := make([]TrailItem, len(parentTrail)+1)
		copy(currentTrail, parentTrail)
		currentTrail[len(parentTrail)] = TrailItem{
			Title: item.Title,
			Path:  path,
		}

		// Get section from the English section map
		section := sectionMap[item.URL]

		// Build trail string
		var trailString string
		if isTopLevel {
			// Top-level pages: use the current page as the trail string
			trailString = item.Title
		} else {
			// Other pages: exclude current page from trail string
			trailForString := currentTrail[:len(currentTrail)-1]
			trailString = buildTrailString(trailForString)
		}

		metadata[item.URL] = PageMetadata{
			Metatags: Metatags{
				Section:     section,
				TrailString: trailString,
			},
			TrailItems: currentTrail, // Always include full trail, including current page
		}

		// Process submenu items
		if len(item.Submenu) > 0 {
			subMetadata := processNavigationForMetadata(item.Submenu, currentTrail, sectionMap, lang)
			maps.Copy(metadata, subMetadata)
		}
	}

	return metadata
}

func buildTrailString(trail []TrailItem) string {
	if len(trail) == 0 {
		return ""
	}

	var titles []string
	for _, item := range trail {
		titles = append(titles, item.Title)
	}

	if len(titles) == 1 {
		return titles[0]
	}

	return strings.Join(titles, " › ")
}

func makeSection(title string) string {
	return strings.ReplaceAll(slug.Make(title), "-", "_")
}

func getLanguages() ([]string, error) {
	pattern := "data/*/navigation.yaml"
	entries, err := filepath.Glob(pattern)
	if err != nil {
		return nil, fmt.Errorf("failed to glob pattern %s: %w", pattern, err)
	}

	var languages []string
	for _, entry := range entries {
		// Extract language code from path like "data/sk/navigation.yaml"
		parts := strings.Split(entry, string(filepath.Separator))
		if len(parts) >= 2 {
			lang := parts[len(parts)-2]       // Get the directory name before navigation.yaml
			if lang != "" && lang != "data" { // Validate extracted language code
				languages = append(languages, lang)
			}
		}
	}

	return languages, nil
}
