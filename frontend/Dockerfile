# Build stage
FROM node:22-alpine AS builder

ARG APP_VERSION=dev
ARG BUILD_DATE

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build with API URL pointing to nginx reverse proxy
ENV VITE_API_URL=/api
ENV VITE_APP_VERSION=$APP_VERSION
ENV VITE_BUILD_DATE=$BUILD_DATE
RUN npm run build-only

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
