<script setup>
import { computed } from "vue";
import {
  GlBadge,
  GlButton,
  GlTooltip,
  GlTooltipDirective as GlTooltip2,
} from "@gitlab/ui";
import languageMappings from "../../../../scripts/supported-code-languages.json";
import { i18n } from "../../../../locales/i18n";
import { useClipboardCopy } from "../utils/use_clipboard_copy";

const props = defineProps({
  codeContent: {
    type: String,
    default: "",
  },
  codeLanguage: {
    type: String,
    default: "",
  },
  // Optional getter returning the code content at copy time. Used by editable
  // code blocks, where the copied text must reflect the reader's live edits
  // rather than a value captured when the component mounted.
  getCodeContent: {
    type: Function,
    default: null,
  },
});

const vGlTooltip = GlTooltip2;

const $t = i18n.t.bind(i18n);

const { copiedStatus, showTooltip, copyToClipboard, copyCodeblock } =
  useClipboardCopy(props);

const codeblockId = `copyCodeblock-${crypto.randomUUID()}`;

const shouldShowLanguage = computed(
  () => props.codeLanguage && !props.codeLanguage.startsWith("plain"),
);

const displayLanguage = computed(
  () => languageMappings[props.codeLanguage] || props.codeLanguage,
);

const buttonClasses = computed(() =>
  shouldShowLanguage.value
    ? "gl-absolute gl-top-5 gl-right-5"
    : "gl-absolute gl-top-4 gl-right-4",
);
</script>

<template>
  <div class="docs-codeblock-toolbar">
    <gl-badge
      v-if="shouldShowLanguage"
      variant="tier"
      class="gl-mb-3 gl-flex gl-w-fit"
      data-testid="code-lang"
    >
      {{ displayLanguage.toLowerCase() }}
    </gl-badge>
    <gl-button
      :id="codeblockId"
      v-gl-tooltip.focus.hover
      :title="$t('clipboard.copyTxt')"
      :aria-label="$t('clipboard.srCopyToClipboard')"
      category="tertiary"
      icon="copy-to-clipboard"
      :class="buttonClasses"
      @click="copyCodeblock"
      @keydown.enter="copyCodeblock"
    />
    <gl-tooltip v-model:show="showTooltip" :target="codeblockId" triggers>
      {{ copiedStatus }}</gl-tooltip
    >
  </div>
</template>
