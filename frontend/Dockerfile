# frontend/Dockerfile - Production Build for Interno Core
# Phase 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build -- --configuration development

# Phase 2: Serve
FROM nginx:stable-alpine
# Copy custom nginx config for SPA support
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/app/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
