import { onUnmounted, ref } from "vue";
import { i18n } from "../../../../locales/i18n";

const $t = i18n.t.bind(i18n);

/**
 * Shared clipboard-copy behavior for the copy buttons.
 *
 * Handles the copy action including "Copied" tooltip state.
 *
 * @param {object} [props] - Owning component's props. Used by `copyCodeblock`
 *   to resolve the code content at click time (`getCodeContent` / `codeContent`).
 */
export function useClipboardCopy(props = {}) {
  const copiedStatus = ref("");
  const showTooltip = ref(false);
  const timeoutId = ref(null);

  // Clean existing timeouts to prevent multiple timeouts
  function clearExistingTimeout() {
    if (timeoutId.value) {
      clearTimeout(timeoutId.value);
      timeoutId.value = null;
    }
  }

  // Reset tooltip value, clear timeouts, add new timeout
  function setResetTimeout() {
    clearExistingTimeout();
    timeoutId.value = setTimeout(() => {
      copiedStatus.value = "";
      timeoutId.value = null;
      showTooltip.value = false;
    }, 1500);
  }

  async function copyToClipboard(typeOfCopy, content) {
    try {
      if (typeOfCopy === "markdown") {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/plain": fetch("index.md")
              .then((response) => {
                if (!response.ok) {
                  throw new Error(
                    `Error getting markdown content: ${response.status}`,
                  );
                }
                return response.text();
              })
              .then((text) => new Blob([text], { type: "text/plain" })),
          }),
        ]);
      } else {
        await window.navigator.clipboard.writeText(content);
      }

      copiedStatus.value = $t("clipboard.copied");
      showTooltip.value = true;
      setResetTimeout();
    } catch (err) {
      console.error("Failed to copy to clipboard:", err);
      copiedStatus.value = "";
    }
  }

  // Resolve the code content at click time (live edits win over the mount-time
  // snapshot) and copy it.
  function copyCodeblock() {
    const content = props.getCodeContent
      ? props.getCodeContent()
      : props.codeContent;
    copyToClipboard("codeblock", content);
  }

  onUnmounted(() => {
    clearExistingTimeout();
  });

  return {
    copiedStatus,
    showTooltip,
    copyToClipboard,
    copyCodeblock,
  };
}
