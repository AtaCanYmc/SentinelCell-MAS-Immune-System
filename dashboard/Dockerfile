FROM --platform=$BUILDPLATFORM node:20-alpine as build
WORKDIR /app

# Install dependencies first for cache layer optimization
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

FROM nginx:alpine
# Fix permissions so Nginx can run as non-root user
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d
RUN touch /var/run/nginx.pid && chown nginx:nginx /var/run/nginx.pid

# Copy the built assets to the Nginx html folder
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Replace main Nginx configuration with our custom config
COPY --chown=nginx:nginx nginx.conf /etc/nginx/nginx.conf
COPY --chown=nginx:nginx conf.d/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

USER nginx

CMD ["nginx", "-g", "daemon off;"]
