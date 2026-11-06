import yaml from "@rollup/plugin-yaml";
import vue from "@vitejs/plugin-vue";
import path from "path";
import copy from "rollup-plugin-copy";
import { defineConfig } from "vite";

const THEME_PATH = "themes/gitlab-docs";
const THEME_GITLAB_UI_DIR = `${THEME_PATH}/static/gitlab_ui`;

const GITLAB_THEME_ASSETS = [
  "@gitlab/ui/dist/index.css*",
  "@gitlab/fonts/gitlab-sans/GitLabSans*.woff2",
  "@gitlab/fonts/gitlab-mono/GitLabMono*.woff2",
  // SVGs we use in CSS
  "@gitlab/svgs/dist/sprite_icons/*",
];

export default defineConfig({
  // Served under /docs/, so lazily loaded chunks live there too.
  base: "/docs/vite/",
  publicDir: false,
  build: {
    outDir: `${THEME_PATH}/static/vite`,
    rollupOptions: {
      input: Object.fromEntries(
        [
          "main.js",
          "page_content.js",
          "landing.js",
          "features/plantuml.js",
          "search/pagefind_search.js",
          "search/pagefind_results.js",
        ].map((file) => [path.basename(file), `${THEME_PATH}/src/${file}`]),
      ),
      output: {
        format: "es",
        inlineDynamicImports: false,
        entryFileNames: "[name]",
        chunkFileNames: "assets/[name].js",
        assetFileNames: `[name].[ext]`,
      },
      // Define static assets we reference from CSS as external.
      // Otherwise Vite flags these as unable to resolve
      external: [
        // Theme icons
        "../fa-icons/youtube.svg",
        // Theme illustrations
        "../favicon.svg",
        "../apple-touch-icon.png",
        "../icon-191.png",
        "../icon-512.png",
        "../ref-arc-arrow-unselected.svg",
        "../ref-arc-arrow-selected.svg",
        "../gitlab-promptling-content-right-facing-purple.png",
        // Fonts
        "../gitlab_ui/fonts/GitLabSans.woff2",
        "../gitlab_ui/fonts/GitLabMono.woff2",
        "../gitlab_ui/fonts/GitLabSans-Italic.woff2",
        "../gitlab_ui/fonts/GitLabMono-Italic.woff2",
        // GitLab SVG icons
        "../gitlab_ui/svgs/external-link.svg",
        "../gitlab_ui/svgs/link.svg",
        "../gitlab_ui/svgs/information-o.svg",
        "../gitlab_ui/svgs/warning.svg",
        "../gitlab_ui/svgs/flag.svg",
        "../gitlab_ui/svgs/review-warning.svg",
        "../gitlab_ui/svgs/ellipsis_h.svg",
        "../gitlab_ui/svgs/error.svg",
        "../gitlab_ui/svgs/question.svg",
        "../gitlab_ui/svgs/chevron-lg-down.svg",
        "../gitlab_ui/svgs/chevron-lg-right.svg",
        "../gitlab_ui/svgs/arrow-up.svg",
        "../gitlab_ui/svgs/arrow-down.svg",
        "../gitlab_ui/svgs/arrow-right.svg",
        "../gitlab_ui/svgs/book.svg",
        "../gitlab_ui/svgs/connected.svg",
        "../gitlab_ui/svgs/tanuki-ai.svg",
        "../gitlab_ui/svgs/compass.svg",
        "../gitlab_ui/svgs/code.svg",
        "../gitlab_ui/svgs/admin.svg",
        "../gitlab_ui/svgs/license.svg",
        "../gitlab_ui/svgs/hamburger.svg",
        "../gitlab_ui/svgs/bullhorn.svg",
        "../gitlab_ui/svgs/sidebar.svg",
        "../gitlab_ui/svgs/appearance.svg",
        "../gitlab_ui/svgs/template.svg",
        "../gitlab_ui/svgs/rss.svg",
        // Favicon Manifest
        "../manifests/manifest.webmanifest",
      ],
    },
  },
  plugins: [
    copy({
      targets: [
        ...GITLAB_THEME_ASSETS.map((file) => {
          const { 1: packageName } = file.split("/");
          return {
            src: `./node_modules/${file}`,
            dest: `${THEME_GITLAB_UI_DIR}/${packageName}`,
          };
        }),
        {
          src: "./node_modules/mermaid/dist/mermaid.min.js",
          dest: `${THEME_PATH}/static/vite`,
        },
        // GitLab UI components need icons.svg available
        // in this location.
        {
          src: "./node_modules/@gitlab/svgs/dist/icons.svg",
          dest: `${THEME_PATH}/static`,
        },
      ],
      copyOnce: true,
      hook: "writeBundle",
    }),
    yaml(),
    vue({
      template: {
        compilerOptions: {
          compatConfig: {
            MODE: 3,
          },
        },
      },
    }),
  ],
  resolve: {
    alias: {
      vue: "@vue/compat",
      "@gitlab/ui": "@gitlab/ui/src",
      "@gitlab/ui/dist": "@gitlab/ui/src",
      "@gitlab/ui/scss": "@gitlab/ui/src/scss",
      "@components": path.resolve(
        __dirname,
        "themes/gitlab-docs/src/components",
      ),
      "@utils": path.resolve(__dirname, "themes/gitlab-docs/src/utils"),
    },
  },
});
