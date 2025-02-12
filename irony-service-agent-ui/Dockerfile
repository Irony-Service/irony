# 1st Stage: Build the Next.js app
FROM node:18 AS builder

WORKDIR /app

# Copy package.json and install dependencies
COPY package.json ./
RUN npm install

# Copy app files and build
COPY . .

# Use ARG instead of ENV
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# 2nd Stage: Serve the built app using a minimal image
FROM node:18-slim

WORKDIR /app

# Copy only the built Next.js output from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules

# Expose the Next.js port
EXPOSE 3000

# Start the Next.js app in production mode
CMD ["npm", "run", "start"]
