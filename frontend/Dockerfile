# Build a self-contained Next.js runtime. NEXT_PUBLIC_API_BASE_URL is embedded
# at build time by Next.js and must be the public HTTPS API origin for releases.
FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM dependencies AS build
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
COPY . ./
RUN npm run build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0
WORKDIR /app
RUN addgroup -S agentos && adduser -S agentos -G agentos
COPY --from=build --chown=agentos:agentos /app/.next/standalone ./
COPY --from=build --chown=agentos:agentos /app/.next/static ./.next/static
USER agentos
EXPOSE 3000
CMD ["node", "server.js"]
