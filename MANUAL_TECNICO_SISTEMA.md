# Manual Técnico y Guía de Arquitectura del Sistema
## Sistema Integral de Control Escolar — Complejo Educativo Santa Sofía

---

## 1. Visión General de la Arquitectura

El sistema está diseñado bajo un enfoque **modular desacoplado**, compuesto por tres capas principales interconectadas mediante protocolos estándar HTTP/REST y JSON:

```
[Portal Web Administrativo (Django 5 / Gunicorn)] ────┐
                                                      │  (Consumo REST Interno :8001)
                                                      ▼
[App Móvil Docente (Flutter / Android)] ──────► [Backend API REST (FastAPI :8001)] ──► [MariaDB :3306]
                                                      ▲
                                                      │
[Internet / Navegadores] ──► [Nginx Proxy + SSL 443] ─┘
```

### Principios Fundamentales de Diseño
1. **Separación de Responsabilidades (SoC):** La lógica de negocio y persistencia reside exclusivamente en la API (`backend`). Ni Django ni Flutter tocan la base de datos MySQL directamente; ambos consumen la API REST.
2. **Escalabilidad Horizontal:** Al estar desacoplados, la API puede balancearse o escalarse independientemente del frontend web o la app móvil.
3. **Consistencia de Datos:** Toda validación de notas, ponderaciones porcentuales (máx 100%) y estados de períodos se centraliza en la API.

---

## 2. Capa de Backend: API REST (FastAPI)

### 2.1 Stack Tecnológico y Librerías
* **Lenguaje:** Python 3.12+
* **Framework:** `FastAPI` (v0.115+)
  - *¿Por qué FastAPI?:* Rendimiento asíncrono ultra-alto (basado en Starlette y ASGI), generación automática de documentación interactiva OpenAPI (Swagger), y serialización estricta con Pydantic.
* **Servidor ASGI:** `Uvicorn` (v0.30+)
  - Manejador de workers asíncronos para sockets de alto rendimiento.
* **ORM:** `SQLAlchemy` (v2.0+)
  - Mapeo objeto-relacional para interactuar con MariaDB mediante clases Python en lugar de SQL crudo concatenado (previniendo inyección SQL).
* **Driver de Base de Datos:** `PyMySQL` + `cryptography`
  - Conector nativo MySQL en Python puro con soporte de autenticación segura `caching_sha2_password` y `mysql_native_password`.
* **Esquemas y Validación:** `Pydantic` (v2.x)
  - Validación de tipos en tiempo de ejecución, parseo de datos entrantes y serialización de respuestas JSON.
* **Gestión de Entorno:** `python-dotenv`
  - Aislamiento de credenciales (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) en archivos `.env`.

### 2.2 Estructura del Código Backend (`/backend/app`)
* **`core/database.py`:** Configura el `engine` de SQLAlchemy, la sesión `SessionLocal` y la función inyectora de dependencias `get_db()`.
* **`models/`:** Modelos de tablas relacionales:
  - `profesor.py`, `estudiantes.py`, `asignatura.py`, `grado_seccion.py`, `periodo.py`, `actividad_evaluativa.py`, `calificacion.py`, `asistencia.py`, `horario.py`, `institucion.py`.
* **`schemas/schemas.py`:** DTOs (Data Transfer Objects) de Pydantic que definen los contratos JSON (`Base`, `Create`, `Response`) para validación de entrada/salida.
* **`routers/`:** Módulos de rutas REST por dominio:
  - `/auth/`: Autenticación institucional por correo y contraseña.
  - `/profesores/`: CRUD de docentes, especialidades y asignaciones.
  - `/estudiantes/`: CRUD de estudiantes, NIE, estado de matrícula.
  - `/secciones/`: Grados escolares (1° a 9°), secciones (A, B) y aulas.
  - `/asignaturas/`: Materias oficiales curriculares.
  - `/periodos/`: Control de los 4 períodos académicos y cierres lectivos.
  - `/actividades/`: Creación de tareas, exámenes y proyectos con ponderación (%) por período.
  - `/calificaciones/`: Registro masivo y unitario de notas (0.00 - 10.00).
  - `/asistencias/`: Pase de lista diario (Presente, Ausente, Justificado).
  - `/institucion/`: Datos del Complejo Educativo Santa Sofía, código MINED y régimen.

---

## 3. Capa Web Administrativa: Portal Django

### 3.1 Stack Tecnológico y Librerías
* **Lenguaje:** Python 3.12+
* **Framework:** `Django` (v5.x / LTS)
  - Provee arquitectura MVC/MVT robusta, motor de plantillas con herencia (`templates/`), control de sesiones seguras (`django.contrib.sessions`), y sistema de seguridad contra ataques CSRF y Clickjacking.
* **Servidor WSGI:** `Gunicorn` (v22+)
  - Servidor HTTP para aplicaciones WSGI en producción en sistemas UNIX/Linux (3 workers en paralelo).
* **Cliente HTTP:** `Requests`
  - Utilizado por `api_client.py` para comunicarse de manera sincrónica con la API de FastAPI.
* **Motor de Generación PDF:** `ReportLab`
  - Usado en `portal/services/reports.py` para construir boletas de notas vectoriales, con encabezados dinámicos, tablas tabuladas con formato MINED y paginación en lotes.
* **UI / Estilos:** TailwindCSS (CDN compilado) + Bootstrap Icons + Boxicons
  - Interfaz moderna, responsive (adaptable a laptops, tablets y móviles) con paneles modales y tablas interactivas.

### 3.2 Arquitectura del Portal Web (`/frontend_web`)
* **Consumo de Datos vía `api_client.py`:**
  En lugar de vincular Django con la base de datos MySQL compartida, Django utiliza `api_client.py` para solicitar datos al backend:
  ```python
  def get_estudiantes():
      r = requests.get(f"{BASE_URL}/estudiantes/", timeout=3)
      return r.json() if r.status_code == 200 else []
  ```
* **Base de Datos Local SQLite (`db.sqlite3`):**
  Django mantiene una base ligera para:
  1. Sesiones de usuario administrativo (`django_session`).
  2. Perfiles y roles locales (`PerfilUsuario`: Director, Secretaria, Docente).
  3. Parámetros de branding institucional en caché (`ConfiguracionInstitucion`).
* **Módulo de Reportes (`reports.py`):**
  - **Generación Individual:** Genera la boleta oficial en formato PDF para un estudiante en particular.
  - **Descarga Masiva por Lote:** Itera sobre todos los alumnos filtrados (por sección o grado) y genera un único documento PDF consolidado con salto de página por cada alumno (`PageBreak()`), listo para impresión masiva en secretaría.

---

## 4. Capa Móvil: App Docente (Flutter)

### 4.1 Stack Tecnológico y Librerías
* **Framework:** `Flutter` (v3.44.8) / Dart SDK (v3.12.2)
  - Compilación nativa Ahead-Of-Time (AOT) en código máquina ARM64 para Android (APK).
* **Librerías principales (`pubspec.yaml`):**
  - `http`: Comunicación asíncrona con la API REST (verbos GET, POST, PUT, DELETE).
  - `shared_preferences`: Almacenamiento local persistente cifrado en disco del teléfono (guarda el token de sesión del profesor y la IP configurable del servidor).
  - `intl`: Formateo de fechas localizadas en español (`es_SV`) para asistencias y calendarios.
  - `google_fonts`: Tipografía moderna (Inter / Poppins) integrada directamente sin dependencias externas.
  - `cupertino_icons`: Iconografía adaptativa.

### 4.2 Arquitectura del Código Móvil (`/app_movil/lib`)
* **`services/api_service.dart`:**
  - Capa de abstracción de red centralizada.
  - Contiene la URL por defecto hacia la nube: `http://130.131.113.202:8001`.
  - Mecanismo dinámico de reconfiguración de IP mediante `SharedPreferences`: el docente o evaluador puede cambiar la IP o dominio del servidor en caliente tocando el badge de seguridad del Login, sin necesidad de recompilar la app.
* **`models/models.dart`:**
  - Clases inmutables con serializadores `fromJson()` y `toJson()` para tipado estricto: `Profesor`, `Estudiante`, `Seccion`, `Asignatura`, `Periodo`, `ActividadEvaluativa`, `Calificacion`, `Asistencia`.
* **`theme/app_theme.dart`:**
  - Implementación de **Material Design 3 con Glassmorphism**:
  - Contenedores translúcidos con desenfoque (`BackdropFilter`), gradientes en tonos Navy Blue (`#1E3A8A`) y acentos de estado (`#10B981` activo, `#EF4444` inactivo).
* **Módulos de Pantallas (`screens/`):**
  1. `login_screen.dart`: Autenticación contra `/auth/login`, validación de rol de docente y almacenamiento seguro del perfil.
  2. `main_navigation_screen.dart`: Navegación principal mediante barra inferior y drawer lateral.
  3. `cursos_screen.dart`: Listado de materias asignadas al profesor logueado.
  4. `calificaciones_screen.dart`: Matriz de calificaciones por actividad; cálculo automático de ponderaciones en tiempo real.
  5. `asistencia_screen.dart`: Pase de lista rápido con botones de selección única (P, A, J) y sincronización inmediata con la API.

---

## 5. Base de Datos Central (MariaDB)

### 5.1 Especificaciones Técnicas
* **Motor:** MariaDB Server 10.11+ / InnoDB
* **Collation / Charset:** `utf8mb4_unicode_ci` (compatibilidad total con caracteres especiales en español, tildes y símbolos).
* **Integridad Referencial:** Claves foráneas con borrado en cascada (`ON DELETE CASCADE`) para evitar registros huérfanos.

### 5.2 Esquema de Tablas Principales
| Tabla | Propósito | Llaves Principales |
|---|---|---|
| `usuarios` | Cuentas del sistema (Director, Secretaria, Profesor) | `id` (PK), `correo` (UNIQUE) |
| `profesores` | Información laboral y especialidad docente | `id` (PK), `usuario_id` (FK a usuarios) |
| `estudiantes` | Matrícula escolar, NIE, datos de contacto | `id` (PK), `nie` (UNIQUE) |
| `grados_secciones` | Organización de salones (ej: 7° Grado "A") | `id` (PK), `aula_id` (FK) |
| `asignaturas` | Materias académicas (Matemáticas, Lenguaje, etc.) | `id` (PK) |
| `periodos_escolares` | Régimen de 4 períodos de evaluación anual | `id` (PK), `estado` (Activo/Inactivo) |
| `actividades_evaluativas` | Tareas, exámenes o laboratorios por materia | `id` (PK), `asignatura_id` (FK), `periodo_id` (FK) |
| `calificaciones` | Nota obtenida por cada alumno en cada actividad | `id` (PK), `estudiante_id` (FK), `actividad_id` (FK) |
| `asistencias` | Registro de presencia/ausencia diaria | `id` (PK), `estudiante_id` (FK), `fecha` |
| `institucion_config` | Datos del Complejo Educativo Santa Sofía | `id` (PK = 1) |

---

## 6. Infraestructura en la Nube y DevOps (Azure)

### 6.1 Especificación del Servidor
* **Proveedor:** Microsoft Azure (Región: `northcentralus`)
* **Máquina Virtual:** `controlEscolar` (Standard_B2als_v2: 2 vCPUs AMD EPYC, 4 GB RAM)
* **Sistema Operativo:** Ubuntu Server 24.04 LTS (Kernel Linux 6.8)
* **IP Pública:** `130.131.113.202`
* **Dominio Oficial FQDN:** `santasofia-escolar.northcentralus.cloudapp.azure.com`

### 6.2 Servicios de Segundo Plano (`systemd`)
Ambos subsistemas se gestionan como demonios de Linux con auto-reinicio si fallan (`Restart=always`):
1. **`escolar-backend.service`:**
   ```ini
   ExecStart=/var/www/control_escolar/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 2
   ```
2. **`escolar-frontend.service`:**
   ```ini
   ExecStart=/var/www/control_escolar/frontend_web/venv/bin/gunicorn core_web.wsgi:application --bind 127.0.0.1:8000 --workers 3
   ```

### 6.3 Configuración del Proxy Inverso (Nginx) y Seguridad SSL
* **Nginx** actúa como punto único de entrada para tráfico web:
  - Puerto 80 (HTTP) redirige automáticamente a HTTPS (301 Permanent Redirect).
  - Puerto 443 (HTTPS) maneja el cifrado TLS 1.3 con certificados oficiales de **Let's Encrypt**.
  - Servidor de archivos estáticos (`/static/` y `/media/`) servidos directamente desde el disco sin pasar por Python, optimizando memoria RAM.
  - Proxy reverso hacia Gunicorn (`http://127.0.0.1:8000`) para todas las vistas web.
* **Seguridad de Red en Azure (Network Security Group - NSG):**
  - **Puerto 22 (SSH):** Gestión remota mediante par de llaves asimétricas RSA (`controlEscolar_key.pem`).
  - **Puerto 80 (HTTP):** Tráfico web no seguro con redirección forzada a 443.
  - **Puerto 443 (HTTPS):** Acceso cifrado al portal web administrativo.
  - **Puerto 8001 (TCP):** Conexión directa de la aplicación móvil Flutter hacia FastAPI.

---

## 7. Cuestionario de Defensa Técnica (Preguntas Difíciles del Evaluador)

### P1: "¿Por qué tienen Django y FastAPI juntos? ¿No es redundante?"
> **Respuesta:** *"No es redundante, responde a una separación clara de patrones de arquitectura: **FastAPI** actúa como el núcleo de microservicio para proveer una API REST pura, ultrarrápida y asíncrona que alimenta tanto la app móvil de los docentes como los servicios externos. **Django** se utiliza como un cliente web corporativo especializado en gestión administrativa, renderizado del portal, control de sesiones y generación masiva de reportes PDF pesados con ReportLab. Si en el futuro cambiamos el portal web por React, Angular o una app de escritorio, la API y la app móvil siguen funcionando intactas sin modificar una sola línea de lógica de negocio ni base de datos."*

### P2: "¿Por qué no conectaron la App Móvil directamente a MySQL?"
> **Respuesta:** *"Por principios elementales de seguridad y arquitectura de software. Conectar una app móvil directamente a una base de datos obligaría a exponer el puerto 3306 a internet y a almacenar credenciales de base de datos dentro del código de la APK, lo que permitiría descompilar la app y hackear la base de datos. Además, la conexión directa carece de control de concurrencia y validación de reglas de negocio. La API REST actúa como una barrera de seguridad (Gateway) que valida tokens, roles y datos antes de tocar el almacenamiento."*

### P3: "¿Cómo evitan que un profesor altere las notas de otro grado o materia?"
> **Respuesta:** *"El control de acceso está validado en la API: cada usuario autenticado tiene un rol (`Director`, `Secretaria`, `Profesor`). Cuando un docente consulta materias o intenta asentar notas, la API filtra las asignaturas cruzando la tabla `profesores` con `horarios` y `grados_secciones`. Si el `profesor_id` no coincide con el asignado a la materia, la solicitud es rechazada con código HTTP 403 Forbidden."*

### P4: "¿Qué pasa si se corta el internet en el colegio mientras el docente califica?"
> **Respuesta:** *"La aplicación Flutter está construida con resiliencia: los datos cargados permanecen en el estado local de la pantalla gracias a los controladores de estado. Si la petición HTTP falla o excede el timeout de 5 segundos, la app captura la excepción, notifica al docente con un SnackBar visual no bloqueante y retiene las notas ingresadas en pantalla para que el docente pueda reintentar la sincronización en cuanto regrese la conectividad."*

### P5: "¿Cómo garantizan la validez de los certificados SSL en producción?"
> **Respuesta:** *"Utilizamos la autoridad certificadora pública **Let's Encrypt** mediante **Certbot** con validación ACME HTTP-01 sobre nuestro FQDN oficial en Azure (`santasofia-escolar.northcentralus.cloudapp.azure.com`). Además, Certbot instaló un temporizador en systemd (`certbot.timer`) que se ejecuta dos veces al día para comprobar y renovar automáticamente los certificados antes de que expiren, garantizando disponibilidad 24/7 sin intervención manual."*
