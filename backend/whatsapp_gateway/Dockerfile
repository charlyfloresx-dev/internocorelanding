FROM node:22-slim

# Install Chromium and its dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    fonts-ipafont-gothic \
    fonts-wqy-zenhei \
    fonts-thai-tlwg \
    fonts-kacst \
    fonts-freefont-ttf \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Skip downloading the bundled chromium by puppeteer and point it to the system chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium

WORKDIR /app

# The build context is /backend, so package.json is at whatsapp_gateway/package.json
COPY whatsapp_gateway/package*.json ./
RUN npm install

COPY whatsapp_gateway/tsconfig.json ./
COPY whatsapp_gateway/src ./src

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
