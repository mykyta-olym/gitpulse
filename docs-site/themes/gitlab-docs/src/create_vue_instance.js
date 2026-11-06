import Vue from "vue";
import { i18n } from "../../../locales/i18n";
/**
 * Create a Vue instance
 */
export const createVueInstance = (el, component, props = {}) => {
  if (!el) return null;

  const instance = new Vue({
    i18n,
    el,
    render: (h) => h(component, { props }),
  });

  // Remove the vue-loading class after the component renders
  instance.$nextTick(() => {
    el.classList.remove("vue-loading");
  });

  return instance;
};
