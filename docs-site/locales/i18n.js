import Vue from "vue";
import VueI18n from "vue-i18n";
import { languages, defaultLocale } from ".";

Vue.use(VueI18n);

/* The locale is the page's, not a constant. This used to be `defaultLocale`
   with nothing ever setting it, so every label the docs shell renders - search,
   feedback, table of contents, the sidebar's own navigation tree - stayed in
   one language whatever the page was written in. Hugo puts the language on
   <html lang>, so read it from there and keep the constant as the fallback for
   a document that somehow has none. */
function pageLocale() {
  const lang = (document.documentElement.lang || "").toLowerCase();
  if (Object.keys(languages).includes(lang)) return lang;
  // `en-GB`, `sk-SK`: match on the primary subtag before giving up.
  const primary = lang.split("-")[0];
  if (Object.keys(languages).includes(primary)) return primary;
  return defaultLocale;
}

const messages = Object.assign(languages);
const i18n = new VueI18n({
  locale: pageLocale(),
  fallbackLocale: "en",
  messages,
});

export { i18n };
