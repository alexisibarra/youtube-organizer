# Frontend Dockerfile
# Keep the major in step with frontend/.nvmrc — CI, the pre-push hook and this
# image must all run the same Node, or `make up` validates a runtime CI never uses.
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# Copy SSL certs for local HTTPS
COPY certs/ /app/certs/

CMD ["npm", "run", "dev"]
