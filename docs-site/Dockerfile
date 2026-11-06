# =============================================================================
# GitPulse documentation - GitLab's current engine (Hugo)
# =============================================================================
# This is gitlab-org/technical-writing/docs-gitlab-com (MIT) - the repository
# that builds docs.gitlab.com today - with its product content mounts removed,
# so it compiles this project's content instead of GitLab's.
#
# Hugo version is pinned to the one their own pipeline uses. Their theme's Sass
# and JS are built by Vite first, exactly as their Makefile does it.
# =============================================================================

# =============================================================================
# Page metadata - GitLab's own generator
# =============================================================================
# The left sidebar, the breadcrumbs and the section highlighting are all built
# from data/<lang>/page-metadata.json, which their Go command derives from
# navigation.yaml. Without it every page reports an empty trail, gets the
# `no-left-nav` body class, and renders with no sidebar at all.
FROM golang:1.25-alpine AS pagemeta

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY cmd/ cmd/
COPY data/ data/
RUN go test ./cmd/... && go run ./cmd/pagemeta

# =============================================================================
FROM hugomods/hugo:exts-0.154.5 AS builder

WORKDIR /build

# The image already carries Node 25 and npm; installing them again collides
# with its existing /usr/local/bin/yarn. What it does NOT carry is corepack, and
# the yarn it does have is 1.22 while this project declares yarn 4.13. Corepack
# is installed to a directory of its own so it never fights that binary.
ENV PATH=/usr/local/corepack/bin:$PATH
RUN npm install -g --prefix /usr/local/corepack corepack@latest

COPY . .
# Every language, not just one. The generator writes one file per language in
# the config, and copying only en-us left the Slovak and English pages with no
# navigation trail - so every page lost its sidebar and breadcrumbs again.
COPY --from=pagemeta /src/data/ data/

# yarn, not npm: their dependency tree relies on yarn's resolution, and npm
# refuses it outright -
#     ERESOLVE  peer vue@^2.7.16 from @gitlab/ui, found vue@3.5.41
# because @gitlab/ui still peers on Vue 2 while the site runs Vue 3.
#
# The install deliberately runs AFTER the source copy rather than before it.
# Installing from the manifests alone is the usual way to keep the dependency
# layer warm, but yarn 4 records its state inside node_modules, and the copy
# that followed left `yarn build` reporting
#     Couldn't find the node_modules state file - running an install might help
RUN corepack enable --install-directory /usr/local/corepack/bin \
    && yarn install --immutable

# Their order: theme assets, then the site that references them.
# --minify matches what their production pipeline emits.
# The icon sprite. Upstream fetches it from a helper script that sources shell
# functions absent in this image, so it failed silently; these are the three
# commands it ran, inlined. That script is not vendored - without icons.svg
# every icon on the site renders blank, including the theme palette's own menu.
RUN npm pack @gitlab/svgs@latest --silent \
    && tar -xzf gitlab-svgs-*.tgz \
    && mkdir -p themes/gitlab-docs/static/gitlab_ui/svgs-latest data \
    && mv package/dist/icons.svg themes/gitlab-docs/static/gitlab_ui/svgs-latest/ \
    && mv package/dist/icons.json data/ \
    && rm -rf package gitlab-svgs-*.tgz

# One search index per access tier, not one over the whole site. A single index
# carried the text of the gated sections, and the role gate lets an index through
# as an asset - so a signed-out visitor could search for a word from the operations
# runbook and read it back. See bin/build-search-indexes.sh.
RUN yarn build \
    && hugo --minify --destination public \
    && sh bin/build-search-indexes.sh public \
    && node bin/fingerprint-assets.mjs public /docs

# =============================================================================
# Production - nginx (same contract as every docs image before it)
# =============================================================================
FROM nginx:alpine AS production

COPY --from=builder /build/public /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80

LABEL org.opencontainers.image.title="GitPulse Documentation" \
      org.opencontainers.image.vendor="TUKE Kosice"

CMD ["nginx", "-g", "daemon off;"]
