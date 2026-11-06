package build

import (
	"testing"

	"github.com/stretchr/testify/require"
	"go.yaml.in/yaml/v3"
)

func TestProcessNavigationForMetadata(t *testing.T) {
	testCases := []struct {
		name           string
		input          string
		lang           string
		expectedOutput map[string]PageMetadata
	}{
		{
			name: "Simple navigation",
			lang: langDefault,
			input: `
- title: Lorem Ipsum
  url: 'dolor/sit/'
  submenu:
    - title: Amet Consectetur
      url: 'dolor/sit/amet/'
    - title: Adipiscing Elit
      url: 'dolor/sit/elit/'
`,
			expectedOutput: map[string]PageMetadata{
				"dolor/sit/": {
					Metatags: Metatags{
						Section:     "lorem_ipsum",
						TrailString: "Lorem Ipsum",
					},
					TrailItems: []TrailItem{
						{Title: "Lorem Ipsum", Path: "dolor/sit/"},
					},
				},
				"dolor/sit/amet/": {
					Metatags: Metatags{
						Section:     "lorem_ipsum",
						TrailString: "Lorem Ipsum",
					},
					TrailItems: []TrailItem{
						{Title: "Lorem Ipsum", Path: "dolor/sit/"},
						{Title: "Amet Consectetur", Path: "dolor/sit/amet/"},
					},
				},
				"dolor/sit/elit/": {
					Metatags: Metatags{
						Section:     "lorem_ipsum",
						TrailString: "Lorem Ipsum",
					},
					TrailItems: []TrailItem{
						{Title: "Lorem Ipsum", Path: "dolor/sit/"},
						{Title: "Adipiscing Elit", Path: "dolor/sit/elit/"},
					},
				},
			},
		},
		{
			name: "Nested navigation",
			lang: langDefault,
			input: `
- title: Sed Do Eiusmod
  url: 'tempor/incididunt/'
  submenu:
    - title: Ut Labore
      url: 'tempor/incididunt/labore/'
    - title: Et Dolore
      url: 'tempor/incididunt/dolore/'
      submenu:
        - title: Magna Aliqua
          url: 'tempor/incididunt/dolore/magna/'
`,
			expectedOutput: map[string]PageMetadata{
				"tempor/incididunt/": {
					Metatags: Metatags{
						Section:     "sed_do_eiusmod",
						TrailString: "Sed Do Eiusmod",
					},
					TrailItems: []TrailItem{
						{Title: "Sed Do Eiusmod", Path: "tempor/incididunt/"},
					},
				},
				"tempor/incididunt/labore/": {
					Metatags: Metatags{
						Section:     "sed_do_eiusmod",
						TrailString: "Sed Do Eiusmod",
					},
					TrailItems: []TrailItem{
						{Title: "Sed Do Eiusmod", Path: "tempor/incididunt/"},
						{Title: "Ut Labore", Path: "tempor/incididunt/labore/"},
					},
				},
				"tempor/incididunt/dolore/": {
					Metatags: Metatags{
						Section:     "sed_do_eiusmod",
						TrailString: "Sed Do Eiusmod",
					},
					TrailItems: []TrailItem{
						{Title: "Sed Do Eiusmod", Path: "tempor/incididunt/"},
						{Title: "Et Dolore", Path: "tempor/incididunt/dolore/"},
					},
				},
				"tempor/incididunt/dolore/magna/": {
					Metatags: Metatags{
						Section:     "sed_do_eiusmod",
						TrailString: "Sed Do Eiusmod › Et Dolore",
					},
					TrailItems: []TrailItem{
						{Title: "Sed Do Eiusmod", Path: "tempor/incididunt/"},
						{Title: "Et Dolore", Path: "tempor/incididunt/dolore/"},
						{Title: "Magna Aliqua", Path: "tempor/incididunt/dolore/magna/"},
					},
				},
			},
		},
		{
			name: "Multiple top-level sections",
			lang: langDefault,
			input: `
- title: First Section
  url: 'first/'
  submenu:
    - title: First Sub
      url: 'first/sub/'
- title: Second Section
  url: 'second/'
  submenu:
    - title: Second Sub
      url: 'second/sub/'
`,
			expectedOutput: map[string]PageMetadata{
				"first/": {
					Metatags: Metatags{
						Section:     "first_section",
						TrailString: "First Section",
					},
					TrailItems: []TrailItem{
						{Title: "First Section", Path: "first/"},
					},
				},
				"first/sub/": {
					Metatags: Metatags{
						Section:     "first_section",
						TrailString: "First Section",
					},
					TrailItems: []TrailItem{
						{Title: "First Section", Path: "first/"},
						{Title: "First Sub", Path: "first/sub/"},
					},
				},
				"second/": {
					Metatags: Metatags{
						Section:     "second_section",
						TrailString: "Second Section",
					},
					TrailItems: []TrailItem{
						{Title: "Second Section", Path: "second/"},
					},
				},
				"second/sub/": {
					Metatags: Metatags{
						Section:     "second_section",
						TrailString: "Second Section",
					},
					TrailItems: []TrailItem{
						{Title: "Second Section", Path: "second/"},
						{Title: "Second Sub", Path: "second/sub/"},
					},
				},
			},
		},
		{
			name: "Simple navigation - English",
			lang: "en",
			input: `
- title: Lorem Ipsum
  url: 'dolor/sit/'
  submenu:
    - title: Amet Consectetur
      url: 'dolor/sit/amet/'
`,
			expectedOutput: map[string]PageMetadata{
				"dolor/sit/": {
					Metatags: Metatags{
						Section:     "lorem_ipsum",
						TrailString: "Lorem Ipsum",
					},
					TrailItems: []TrailItem{
						{Title: "Lorem Ipsum", Path: "en/dolor/sit/"},
					},
				},
				"dolor/sit/amet/": {
					Metatags: Metatags{
						Section:     "lorem_ipsum",
						TrailString: "Lorem Ipsum",
					},
					TrailItems: []TrailItem{
						{Title: "Lorem Ipsum", Path: "en/dolor/sit/"},
						{Title: "Amet Consectetur", Path: "en/dolor/sit/amet/"},
					},
				},
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			var navigation []NavItem
			err := yaml.Unmarshal([]byte(tc.input), &navigation)
			require.NoError(t, err, "Error parsing YAML")

			// Create section map like the real function does
			sectionMap := make(map[string]string)
			for _, item := range navigation {
				section := makeSection(item.Title)
				mapPathsToSection([]NavItem{item}, section, sectionMap)
			}

			result := processNavigationForMetadata(navigation, []TrailItem{}, sectionMap, tc.lang)
			require.Equal(t, tc.expectedOutput, result, "Unexpected result from processNavigationForMetadata")
		})
	}
}

func TestMakeSection(t *testing.T) {
	testCases := []struct {
		name     string
		input    string
		expected string
	}{
		{
			name:     "Simple title",
			input:    "Getting Started",
			expected: "getting_started",
		},
		{
			name:     "Title with hyphens",
			input:    "CI/CD Pipeline",
			expected: "ci_cd_pipeline",
		},
		{
			name:     "Title with special characters",
			input:    "API & Integration",
			expected: "api_and_integration",
		},
		{
			name:     "Title with numbers",
			input:    "Version 2.0 Guide",
			expected: "version_2_0_guide",
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result := makeSection(tc.input)
			require.Equal(t, tc.expected, result, "Unexpected result from makeSection")
		})
	}
}
