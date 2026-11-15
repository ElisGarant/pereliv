# Собирает Mini App и отдаёт его через Caddy с автоматическим HTTPS
FROM node:22-alpine AS build
WORKDIR /web
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM caddy:2.8-alpine
COPY --from=build /web/dist /srv/web
COPY Caddyfile /etc/caddy/Caddyfile
