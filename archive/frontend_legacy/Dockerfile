# Etapa 1: Construcción (Build)
FROM node:20-alpine AS build

WORKDIR /app

# Instalación de dependencias
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copia de código y compilación
COPY . .
RUN npx ng build --configuration=production

# Etapa 2: Servidor de Producción (Nginx)
FROM nginx:alpine

# Limpieza de archivos por defecto
RUN rm -rf /usr/share/nginx/html/*

# Copia de los archivos compilados
COPY --from=build /app/dist/app/browser /usr/share/nginx/html

# --- INTEGRACIÓN FUNCIONAL ---
# Copiar la configuración del Reverse Proxy
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]