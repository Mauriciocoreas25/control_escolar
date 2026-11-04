# Manual de Usuario del Sistema de Control Escolar
## Complejo Educativo Santa Sofía

---

## 1. Introducción y Canales de Acceso

Bienvenido al **Sistema Integral de Control Escolar del Complejo Educativo Santa Sofía**. Esta plataforma permite la administración académica centralizada, matrícula de estudiantes, registro de calificaciones, pase de asistencia y emisión oficial de boletas de evaluación.

### 1.1 Direcciones de Acceso
* **Portal Web Administrativo:**
  👉 **https://santasofia-escolar.northcentralus.cloudapp.azure.com**
  *(Compatible con Chrome, Edge, Safari, Firefox en computadoras y tablets)*.
* **Aplicación Móvil para Docentes (Android):**
  👉 Archivo instalable: `SantaSofia_Docente.apk`

### 1.2 Roles del Sistema y Credenciales de Ejemplo
| Rol | Alcance | Cuenta de Prueba | Contraseña |
|---|---|---|---|
| **Director General** | Acceso total a auditoría, configuración institucional, usuarios, cierres de período y reportes. | `director@santasofia.edu.sv` | `admin123` |
| **Secretaría Académica** | Matrícula de estudiantes, asignación de secciones, emisión de boletas de calificaciones y reportes. | `secretaria@santasofia.edu.sv` | `secretaria123` |
| **Profesor / Docente** | Pase de asistencia diario, creación de tareas/exámenes y registro de notas (Web y App Móvil). | `carlos.docente@santasofia.edu.sv` | `docente123` |

---

## 2. Portal Web Administrativo

### 2.1 Inicio de Sesión
1. Abra el navegador e ingrese a **https://santasofia-escolar.northcentralus.cloudapp.azure.com**.
2. Ingrese su **Correo Institucional** y **Contraseña**.
3. Haga clic en el botón **"Iniciar Sesión"**.
4. El sistema lo redirigirá automáticamente al Panel de Control según su perfil asignado.

---

### 2.2 Panel de Control (Dashboard)
El panel principal presenta un resumen ejecutivo en tiempo real:
* **Tarjetas de Estadísticas (KPIs):** Total de estudiantes matriculados, número de profesores activos, secciones escolares y porcentaje de asistencia global.
* **Período Lectivo Activo:** Muestra el período académico en curso (Período 1, 2, 3 o 4) y el año lectivo oficial (2026).
* **Accesos Rápidos:** Botones de un solo clic para matricular alumnos, registrar notas y emitir boletas.

---

### 2.3 Módulo de Estudiantes
Ubicación: Menú lateral ➔ **Estudiantes**

#### A. Registrar un Nuevo Estudiante:
1. Haga clic en el botón azul **"Registrar Nuevo Estudiante"**.
2. Complete el formulario con los datos obligatorios:
   * **NIE:** Número de Identificación Estudiantil único (ej: `10234567`).
   * **Nombres y Apellidos Completos.**
   * **Grado y Sección:** Seleccione el salón asignado (ej: 7° Grado "A").
   * **Fecha de Nacimiento y Género.**
   * **Datos del Responsable:** Nombre del padre/madre/tutor y teléfono de contacto.
3. Presione **"Guardar Estudiante"**.

#### B. Modificar o Dar de Baja:
* En la tabla de estudiantes, use el buscador superior por NIE o nombre.
* En la columna de acciones:
  * ✏️ **Editar:** Para actualizar teléfonos, dirección o cambiar de sección.
  * ❌ **Eliminar / Estado:** Para marcar al estudiante como inactivo o retirado.

---

### 2.4 Módulo de Docentes y Asignaturas
Ubicación: Menú lateral ➔ **Docentes** / **Asignaturas**

* **Gestión de Profesores:** Permite dar de alta a nuevos maestros con su correo institucional, especialidad (ej. Matemáticas, Ciencias) y teléfono.
* **Asignación de Carga Académica:** Permite vincular qué profesor imparte qué materia en cada grado y sección específica.

---

### 2.5 Módulo de Períodos Escolares
Ubicación: Menú lateral ➔ **Períodos**

El régimen académico anual se divide en **4 Períodos**:
* **Estado "Activo":** Permite a los docentes crear actividades evaluativas y subir notas.
* **Estado "Inactivo" (Cerrado):** Bloquea la edición de notas de períodos anteriores para proteger la integridad del historial académico.
* Para abrir o cerrar un período, la Dirección o Secretaría simplemente hace clic en el interruptor de estado.

---

### 2.6 Calificaciones y Actividades Evaluativas
Ubicación: Menú lateral ➔ **Calificaciones**

1. Seleccione el **Grado/Sección**, la **Materia** y el **Período**.
2. **Crear Actividad Evaluativa:**
   * Haga clic en **"Nueva Actividad"**.
   * Ingrese el nombre (ej: *Examen Trimestral*, *Laboratorio 1*, *Tarea de Investigación*).
   * Asigne la **Ponderación Porcentual** (la suma de actividades del período no debe exceder el 100%).
3. **Asentar Notas:**
   * Aparecerá la lista de estudiantes del grado seleccionado.
   * Digite las notas en escala de **0.00 a 10.00**.
   * Presione **"Guardar Calificaciones"**. El sistema recalcula promedios automáticamente.

---

### 2.7 Emisión y Descarga de Boletas de Calificaciones
Ubicación: Menú lateral ➔ **Boletas**

Este módulo permite consultar los consolidados de notas y emitir documentos oficiales.

#### Filtros de Búsqueda:
* Seleccione la **Sección Escolar** (ej. 7° Grado "A") y el **Período**.
* La tabla mostrará a los alumnos, su promedio ponderado y su estado académico.

#### Opciones de Descarga:
1. **Descargar Boleta Individual:**
   * En la fila de cualquier estudiante, haga clic en el botón de descarga PDF.
   * Se genera la boleta oficial membretada con formato MINED para ese alumno.
2. **Descarga Masiva por Lotes ("Descargar Lote PDF"):**
   * Haga clic en el botón superior **"Descargar Lote PDF"**.
   * El sistema procesará a todos los estudiantes de la sección y descargará un **único archivo PDF continuo**.
   * Cada estudiante tiene su propia página independiente (`PageBreak`), listo para imprimir el lote completo del salón de una sola vez sin abrir archivo por archivo.
3. **Exportar a Excel:**
   * Descarga la matriz tabular con todas las notas para análisis estadístico.

---

### 2.8 Pase de Asistencia Diario
Ubicación: Menú lateral ➔ **Asistencia**

1. Seleccione la fecha y la sección.
2. Marque a cada alumno con:
   * **P (Verde):** Presente.
   * **A (Rojo):** Ausente.
   * **J (Amarillo):** Falta Justificada.
3. Haga clic en **"Guardar Asistencia"**.

---

## 3. Aplicación Móvil para Docentes (Android)

La aplicación móvil permite a los profesores gestionar sus clases de forma rápida desde cualquier teléfono inteligente Android, incluso dentro del aula de clases.

### 3.1 Instalación en el Teléfono
1. Transfiera el archivo **`SantaSofia_Docente.apk`** a su teléfono (por WhatsApp, cable USB o Google Drive).
2. Toque el archivo descargado para iniciar la instalación.
3. Si Android muestra la advertencia *"Por motivos de seguridad, tu teléfono no tiene permitido instalar apps desconocidas"*:
   * Toque **Ajustes** ➔ Active **"Permitir desde esta fuente"** ➔ Vuelva atrás y toque **Instalar**.
4. Abra la aplicación **"Santa Sofía Docente"**.

---

### 3.2 Conexión y Login
1. **Verificación de Servidor:**
   * En la parte inferior de la pantalla de bienvenida verá el indicador:
     *`Conexión Segura • Servidor Escolar Activo`*.
   * *(Opcional: Si el colegio cambia de IP en el futuro, puede tocar esa barra para actualizar la dirección del servidor).*
2. **Ingreso de Credenciales:**
   * **Correo:** `carlos.docente@santasofia.edu.sv` *(o el correo propio del profesor)*.
   * **Contraseña:** `docente123`.
3. Toque **"Ingresar a la Plataforma"**.

---

### 3.3 Funcionalidades Principales de la App Móvil

#### A. Mis Cursos Asignados
* En la pantalla principal, el docente verá únicamente los grados y materias que tiene asignados (ej. *Matemáticas - 7° "A"*).
* Al tocar un curso se desplegarán las opciones de **Calificaciones**, **Asistencia** y **Estudiantes**.

#### B. Registro Rápido de Calificaciones
1. Seleccione la materia y el período activo.
2. Seleccione la actividad evaluativa creada o agregue una nueva.
3. Ingrese la calificación correspondiente a cada alumno con el teclado numérico.
4. Toque **"Guardar Notas"** para sincronizar con la base de datos central en la nube.

#### C. Pase de Lista Móvil (Asistencia en el Aula)
1. Abra la opción **"Tomar Asistencia"**.
2. El sistema muestra la lista de alumnos con botones táctiles:
   * **P** (Presente)
   * **A** (Ausente)
   * **J** (Justificado)
3. Al finalizar, toque el botón flotante de confirmación. Los registros se reflejan inmediatamente en el portal web de la secretaría y dirección.

---

## 4. Preguntas Frecuentes y Soporte (FAQ)

### ¿Qué debo hacer si olvido mi contraseña?
Contacte a la Secretaría Académica o al Director General. Desde el módulo de **Usuarios** en el portal web, ellos pueden restablecer su contraseña institucional en segundos.

### ¿Por qué el sistema no me deja registrar una nota mayor a 10.00?
El sistema aplica validaciones pedagógicas oficiales del Ministerio de Educación (MINED): la escala de calificación permitida es de **0.00 a 10.00**. Cualquier valor superior es rechazado automáticamente por la API.

### ¿Cómo descargo las boletas de un grado entero sin abrir alumno por alumno?
En el módulo de **Boletas**, seleccione el grado (ej. 7° A) y presione el botón superior **"Descargar Lote PDF"**. El sistema compilará un solo documento con todas las boletas individuales paginadas para imprimir directamente.

### ¿La aplicación móvil consume muchos datos móviles?
No. La app utiliza el protocolo REST con intercambio de datos en formato JSON ligero (menos de 50 KB por sincronización), lo que garantiza un consumo mínimo de datos celulares y máxima velocidad.
