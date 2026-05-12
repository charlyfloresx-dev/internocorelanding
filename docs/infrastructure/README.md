# 🏗️ ADN de Infraestructura

Este directorio contiene las especificaciones y herramientas necesarias para desplegar el ecosistema InternoCore en la nube o en servidores privados.

## 📁 Estructura
- **[Recetas (Recipes)](./recipes/)**: Archivos JSON y políticas extraídas de la infraestructura real de AWS. Es el "backup" de la topología de red y seguridad.
- **[Guías (Guides)](./guides/)**: Manuales paso a paso para la resurrección del entorno y el uso de scripts de despliegue.

## 🚀 Despliegue Universal
El archivo clave para la recuperación ante desastres o escalado es:
`docs/infrastructure/guides/deploy_to_new_aws_account.ps1`

Este script permite recrear toda la infraestructura en una cuenta AWS virgen sin dependencias de IDs anteriores.
