<script>
import { GlCollapsibleListbox } from "@gitlab/ui";

export default {
  components: {
    GlCollapsibleListbox,
  },
  props: {
    languages: {
      type: Array,
      required: true,
    },
    currentLang: {
      type: String,
      required: true,
    },
  },
  data() {
    return {
      selectedLanguage: this.currentLang,
    };
  },
  computed: {
    formattedItems() {
      return [
        {
          text: this.$t("languageSelector.language"),
          options: this.languages.map((lang) => ({
            value: lang.code,
            text: lang.name,
          })),
        },
      ];
    },
  },
  methods: {
    onLanguageSelect(value) {
      const selectedItem = this.languages.find((lang) => lang.code === value);
      if (selectedItem?.url) {
        // Record the choice so it persists and OUTRANKS the language inherited
        // from the application (preferences.js). This is the reader explicitly
        // choosing a documentation language while looking at the docs; without
        // it the app's `gp_lang` would override the pick on the next load.
        try {
          localStorage.setItem(
            "gitpulse-docs-lang",
            String(value).slice(0, 2).toLowerCase(),
          );
        } catch {
          /* private mode - the pick still applies this navigation */
        }
        // Preserve anchor links when switching languages
        const currentHash = window.location.hash;
        const targetUrl = currentHash
          ? `${selectedItem.url}${currentHash}`
          : selectedItem.url;
        window.location.href = targetUrl;
      }
    },
  },
};
</script>

<template>
  <gl-collapsible-listbox
    class="language-selector gl-my-3 gl-flex lg:gl-my-0"
    icon="earth"
    :selected="selectedLanguage"
    :items="formattedItems"
    placement="bottom-start"
    @select="onLanguageSelect"
  />
</template>
