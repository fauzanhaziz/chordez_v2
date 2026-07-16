FROM node:20-alpine

WORKDIR /app

# Copy package file dan install dependensi
COPY package*.json ./
RUN npm install

# Copy seluruh source code frontend
COPY . .

# Build aplikasi Next.js
RUN npm run build

# Buka port 3000 untuk Next.js
EXPOSE 3000

# Jalankan aplikasi
CMD ["npm", "run", "start"]