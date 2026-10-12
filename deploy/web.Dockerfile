# AuthentiQ website (/) and admin portal (/admin/), served by nginx, which also proxies /api.
# Build context: the repository root.

FROM node:22-bookworm AS build
RUN npm install -g bun@1.4.2
WORKDIR /src

COPY frontend/package.json frontend/bun.lock frontend/bunfig.toml ./frontend/
RUN cd frontend && bun install --frozen-lockfile
COPY admin/package.json admin/bun.lock ./admin/
RUN cd admin && bun install --frozen-lockfile

COPY frontend ./frontend
COPY admin ./admin

# Empty = call the API on the same site (nginx below proxies /api to the backend).
ARG VITE_API_URL=""
ENV VITE_API_URL=${VITE_API_URL}
RUN cd frontend && python3 scripts/build-single-html.py
RUN cd admin && bun run build

FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/security-headers.inc /etc/nginx/snippets/security-headers.inc
COPY --from=build /src/frontend/dist-single/authentiq.html /usr/share/nginx/html/index.html
COPY --from=build /src/frontend/public/media /usr/share/nginx/html/media
COPY --from=build /src/admin/dist /usr/share/nginx/html/admin
EXPOSE 80
