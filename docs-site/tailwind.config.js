/* eslint-disable import/no-default-export */
import defaultPreset from "@gitlab/ui/tailwind.defaults";

/** @type {import('tailwindcss').Config} */
export default {
  presets: [defaultPreset],
  content: [
    "themes/**/*.html",
    "themes/**/*.vue",
    "node_modules/@gitlab/ui/src/components/**/*.vue",
  ],
  theme: {
    extend: {
      width: {
        limited: "1006px",
      },
    },
  },
};
