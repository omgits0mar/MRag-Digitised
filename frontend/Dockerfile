# syntax=docker/dockerfile:1.7

# -----------------------------------------------------------------------------
# Stage 1 — build the Vite bundle.
# VITE_API_BASE_URL is baked in at build time; same-origin /api means the
# browser hits nginx which proxies to the backend service on the compose net.
# -----------------------------------------------------------------------------
FROM node:20-alpine AS build

ENV VITE_API_BASE_URL=/api \
    VITE_ENABLE_MOCK=false \
    VITE_ENABLE_STREAMING=true \
    VITE_DEFAULT_MODEL=llama3-8b-8192 \
    VITE_API_REQUEST_TIMEOUT_MS=120000

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2 — nginx serving the static bundle with SPA fallback + /api proxy.
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS serve

RUN rm -f /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
