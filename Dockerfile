FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm config set fetch-retry-maxtimeout 600000 && \
    npm config set fetch-retries 10 && \
    npm install --no-audit --no-fund && \
    npm cache clean --force

# Copy application files
COPY . .

# Build the application
RUN npm run build

# Expose port (adjust if your production server runs on a different port)
EXPOSE 5000

# Start the server
CMD ["npm", "run", "start"]
