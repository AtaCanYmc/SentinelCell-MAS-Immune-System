FROM node:20-alpine as build
WORKDIR /app

# Install dependencies first for cache layer optimization
COPY package*.json ./
RUN npm ci

# Copy source code and build
COPY . .
RUN npm run build

FROM nginx:alpine
# Copy the built assets to the Nginx html folder
COPY --from=build /app/dist /usr/share/nginx/html

# Replace default Nginx configuration with our custom config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
