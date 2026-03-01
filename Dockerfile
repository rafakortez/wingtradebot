# Stage 1: Application Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package*.json ./
COPY tsconfig*.json ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Copy source code
COPY src/ ./src/

# TypeScript requires an existing config file for the build
# We copy the example just to satisfy the compiler for the production build
COPY src/config.example.ts ./src/config.ts

# Compile TypeScript
RUN npm run build

# ==========================================

# Stage 2: Clean Production Image
FROM node:20-alpine AS runner

WORKDIR /app

# Set Node to Production environment (optimizes Express dependencies, etc.)
ENV NODE_ENV=production

# Copy only base manifests again
COPY package*.json ./

# Install ONLY vital Production dependencies (ignoring Jest, TypeScript docs...) - keeps image light
RUN npm ci --only=production

# Copy only the actually compiled code folder (clean, performant Javascript)
COPY --from=builder /app/dist ./dist

# EXPOSE documentation
EXPOSE 443 80

# Command to run the application directly (as defined in package.json)
CMD ["npm", "run", "start:direct"]
