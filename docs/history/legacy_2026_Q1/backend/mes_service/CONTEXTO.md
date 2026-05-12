# Contexto de Negocio: mes_service

## 🎯 Objetivo
El microservicio MES es el puente entre la operación física (piso) y la inteligencia de datos. Su misión es capturar cada evento de producción y paro para calcular la eficiencia real (OEE).

## 🏭 La Regla de Oro de Piso
*"Si el sistema se cae, la línea no se detiene"*. Esto implica que el sistema debe ser resiliente y permitir el registro offline cuando sea necesario.

## 📊 Propuesta de Valor
- **Trazabilidad Triple:** Identidad técnica, secuencia interna y folio comercial.
- **Transparencia en Tiempo Real:** Dashboard para supervisores con KPIs actualizados al instante.
- **Integración Nativa:** Conexión con WMS para Backflush automático al declarar producción.

## 📝 Alcance MVP (Fase Actual)
1. **Turnos Flexibles:** Definición dinámica por recurso (Línea/Celda/Máquina) y empresa.
2. **Escalación Crítica:** Motor de notificaciones cada 5 minutos sobre paros activos.
3. **Capacidad Dinámica:** Ajuste de meta horaria basado en personal presente vs planeado.
4. **Captura Híbrida:** Terminales PC con input manual y soporte para scanners industriales.
5. **Planeación Realista:** Módulo "Material-Aware" que sugiere producción según disponibilidad sin bloquear la operación (No-Stop Policy).

## 🚀 Próximos Pasos (Post-MVP)
- Integración con PLC y sensores (IoT).
- Autenticación biográfica/RFID en terminales de piso.
- Sincronización offline (Edge Sidecar).
