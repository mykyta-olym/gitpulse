<script setup>
import { computed, ref } from "vue";
import { GlDisclosureDropdown, GlIcon } from "@gitlab/ui";
import { i18n } from "../../../../locales/i18n";
import { useClipboardCopy } from "../utils/use_clipboard_copy";

const $t = i18n.t.bind(i18n);

const { copiedStatus, copyToClipboard } = useClipboardCopy();

const dropdownRef = ref(null);

// With auto-close disabled, close manually only for the external-link items so
// the "Copy as Markdown" action can keep the dropdown open to show its status.
const onAction = (item) => {
  if (item.href) {
    dropdownRef.value?.close();
  }
};

const currentMarkdownURL = new URL("index.md", window.location.href).href;

const createAgentToolQuery = (toolURL) => {
  return `${toolURL}?q=${encodeURIComponent(`Read from ${currentMarkdownURL} and answer my follow-up questions about it.`)}`;
};

const dropdownGroups = computed(() => [
  {
    items: [
      {
        // What the action segment used to do, first in the list.
        text: $t("copyForLLMOptions.copyMarkdownButton"),
        action: () => copyToClipboard("markdown"),
        icon: "copy-to-clipboard",
      },
      {
        text: $t("copyForLLMOptions.viewMarkdownButton"),
        href: currentMarkdownURL,
        extraAttrs: {
          target: "_blank",
          rel: "noopener noreferrer",
        },
      },
    ],
  },
  {
    items: [
      {
        text: $t("copyForLLMOptions.openInClaude"),
        href: createAgentToolQuery("https://claude.ai/new"),
        extraAttrs: {
          target: "_blank",
          rel: "noopener noreferrer",
        },
      },
      {
        text: $t("copyForLLMOptions.openInChatGPT"),
        href: createAgentToolQuery("https://chatgpt.com"),
        extraAttrs: {
          target: "_blank",
          rel: "noopener noreferrer",
        },
      },
    ],
  },
]);
</script>

<template>
  <!--
    One shape, the same as the Edit menu beside it.

    This was a split button - an action segment that copied on click, and a
    chevron segment that opened the menu - next to a plain dropdown. Same width,
    same height, same colours, and still obviously two different controls,
    because one carried a seam down its middle and the other did not. Two
    buttons stacked in one rail should read as one set.

    Nothing is hidden by the change: the plain copy is the FIRST item of the
    menu, above the variants it always sat beside.
  -->
  <gl-disclosure-dropdown
    ref="dropdownRef"
    class="gl-w-full"
    :items="dropdownGroups"
    :toggle-text="copiedStatus || $t('copyForLLMOptions.copyForLLM')"
    icon="copy-to-clipboard"
    block
    @action="onAction"
  >
    <template #list-item="{ item }">
      <span class="gl-flex gl-items-center gl-justify-between gl-gap-3">
        {{ item.text }}
        <gl-icon v-if="item.icon" :name="item.icon" />
        <gl-icon v-else-if="item.href" name="external-link" />
      </span>
    </template>
  </gl-disclosure-dropdown>
</template>
