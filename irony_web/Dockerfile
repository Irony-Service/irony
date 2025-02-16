FROM nginx:alpine

# Copy the static website files
COPY . /usr/share/nginx/html/

# Copy nginx configuration
COPY ../nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 8080
EXPOSE 8080

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
