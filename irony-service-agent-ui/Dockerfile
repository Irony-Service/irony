# 1st Stage: Build the Next.js app
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy app files and build
COPY . .

# Enable standalone mode in Next.js
RUN npm run build

# 2nd Stage: Serve the built app using a minimal image
FROM node:18-alpine

WORKDIR /app

# Copy only the standalone output
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
COPY --from=builder /app/.env.production ./.env.production

# Expose the Next.js port
EXPOSE 3000

# Start the Next.js standalone server
CMD ["node", "server.js"]
