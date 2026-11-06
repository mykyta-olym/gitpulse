import postcssImport from "postcss-import";

export default {
  plugins: {
    "postcss-import": postcssImport({
      path: ["node_modules", "themes/gitlab-docs/src/css"],
    }),
    "tailwindcss/nesting": {},
    tailwindcss: {},
    autoprefixer: {},
  },
};
