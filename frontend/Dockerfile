# Build the standalone server. next/font downloads Geist here, so this needs internet.
FROM node:24-slim AS build
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# The runtime image has only what the server needs, and does not run as root.
FROM node:24-slim
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
COPY --from=build --chown=node:node /app/.next/standalone ./
# The standalone server does not include static files; they must be copied.
COPY --from=build --chown=node:node /app/.next/static .next/static
USER node
EXPOSE 3000
CMD ["node", "server.js"]
