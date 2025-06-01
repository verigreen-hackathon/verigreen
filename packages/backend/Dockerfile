# 1. Use official Node.js LTS image
FROM node:18-alpine

# 2. Set working directory
WORKDIR /app

# 4. Copy the rest of the app
COPY . .

# 3. Copy package files and install dependencies
RUN npm install

# 5. Set environment variables (optionally overridden in docker-compose or CLI)
ENV NODE_ENV=production
ENV PORT=3000

# 6. Generate Prisma Client (MongoDB doesn't support migrate, only generate)
RUN npx prisma generate

# 7. Build the app (assuming it's a TypeScript project)
RUN npm run build

# 8. Expose the port your app runs on (e.g., 3000)
EXPOSE 3000

# 9. Start the app
CMD ["npm", "run", "start"]
