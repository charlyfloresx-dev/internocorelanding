# Manual de Operaciones - InternoCore Event Engine

## v2.0 - Motor de Quórum Generalizado

### 📊 Gestión de Quórum (Aprobación)
El sistema ahora utiliza un motor de quórum dinámico ($N$-Aprobadores). Para que una foto sea pública en la galería y se envíe a imprimir, debe recibir el visto bueno de $N$ personas/dispositivos distintos.

#### 🛡 El Filtro de Integridad
Para evitar fraudes o errores humanos, el sistema rastrea el ID del dispositivo. 
- **Regla de Oro**: Un mismo teléfono no puede aprobar dos veces la misma foto, incluso si usa links de aprobadores distintos.
- **Acción recomendada**: Entregue el QR de "Aprobador #1" a una persona y el QR de "Aprobador #2" a otra persona física con su propio dispositivo móvil.

### 🛠 Dashboard de Staff (Moderación)
El personal de staff tiene acceso al panel de control (`/staff/dashboard`) para monitorear la salud del evento.

#### 🔄 Reinicio de Quórum (Reset)
Si un aprobador comete un error y valida una foto que no cumple con los estándares, el Staff puede intervenir:
1. Localice la foto en la **Galería en Curso** del Dashboard.
2. Pase el mouse (o presione) sobre la foto para ver las acciones.
3. Use el botón **Reiniciar Quórum** (icono de retorno).
4. El contador de la foto volverá a **0** y desaparecerá de la galería pública hasta que el ciclo de votación se complete de nuevo correctamente.

### 📸 Configuración del Evento (Setup)
Al iniciar un nuevo evento, el sistema preguntará:
- **Número de Aprobadores**: Defina cuántas validaciones requiere cada foto.
  - *Social (Boda)*: Sugerido 2 (Novio y Novia).
  - *Corporativo*: Sugerido 1 o 2 (Marketing / Legal).
  - *Eventos Masivos*: Sugerido 1 para rapidez.

### ⚠️ Solución de Problemas
- **"Este dispositivo ya ha aprobado esta foto"**: Esto significa que el usuario está intentando suplantar a otro aprobador desde el mismo teléfono. Pida a un segundo responsable que use su propio dispositivo.
- **La foto no aparece en imprimir**: Verifique el progreso del quórum en el app de aprobación. Los puntos grises deben volverse dorados.
