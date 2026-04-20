FROM prom/prometheus:v2.45.0

# Copiamos nuestra configuración de scraping
COPY prometheus.yml /etc/prometheus/prometheus.yml

# Configuramos retención corta de 7 días (para reducir costos en EBS/S3)
# y limitamos el tamaño máximo para prevenir desbordamientos locales
CMD [ \
  "--config.file=/etc/prometheus/prometheus.yml", \
  "--storage.tsdb.path=/prometheus", \
  "--storage.tsdb.retention.time=7d", \
  "--storage.tsdb.retention.size=5GB", \
  "--web.console.libraries=/usr/share/prometheus/console_libraries", \
  "--web.console.templates=/usr/share/prometheus/consoles" \
]

EXPOSE 9090
