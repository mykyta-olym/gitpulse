import en from "./en.json";
import sk from "./sk.json";

export const defaultLocale = "sk";

// The languages this site publishes. `SidebarMenu` also checks this list before
// resolving `data/<locale>/navigation.yaml`, so a language missing here silently
// falls back to another language's navigation tree.
export const languages = {
  sk,
  en,
};
