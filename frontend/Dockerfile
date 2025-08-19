# Frontend Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Copy SSL certs for local HTTPS
COPY certs/ /app/certs/

CMD ["npm", "run", "dev"]
