-- Creación de la Base de Datos
CREATE DATABASE IF NOT EXISTS control_escolar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE control_escolar_db;

-- 1. Tabla de Usuarios y Roles (RBAC: Director, Secretaria, Profesor, etc.)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('Director', 'Secretaria', 'Profesor') NOT NULL,
    estado BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Aulas e Infraestructura
CREATE TABLE IF NOT EXISTS aulas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,          -- Ej: 'A-101', 'LAB-COMP', 'TALLER-1'
    nombre VARCHAR(100) NOT NULL,                 -- Ej: 'Salón 1 - Pabellón A', 'Laboratorio de Ciencias'
    tipo ENUM('Estandar', 'Laboratorio', 'Taller', 'Cancha', 'Auditorio', 'Otro') NOT NULL DEFAULT 'Estandar',
    capacidad INT NULL,
    ubicacion VARCHAR(150) NULL,
    estado BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabla de Grados y Secciones (El aula base pertenece a la sección)
CREATE TABLE IF NOT EXISTS grados_secciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grado VARCHAR(50) NOT NULL,                  -- Ej: 'Primer Grado', 'Noveno Grado'
    seccion VARCHAR(10) NOT NULL,                 -- Ej: 'A', 'B'
    anio_lectivo INT NOT NULL,                    -- Ej: 2026
    aula_base_id INT NULL,                        -- Aula física fija asignada a la sección
    FOREIGN KEY (aula_base_id) REFERENCES aulas(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uk_grado_seccion (grado, seccion, anio_lectivo),
    -- Regla de Negocio: Un aula física no puede estar asignada a dos secciones en el mismo ciclo lectivo
    UNIQUE KEY uk_aula_base_anio (aula_base_id, anio_lectivo)
);

-- 4. Tabla de Profesores (Vinculada al usuario con rol Profesor)
CREATE TABLE IF NOT EXISTS profesores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    telefono VARCHAR(20),
    especialidad VARCHAR(100),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
);

-- 5. Tabla de Encargados (Padres, madres o tutores)
CREATE TABLE IF NOT EXISTS encargados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombres VARCHAR(150) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    telefono VARCHAR(20) NOT NULL,
    direccion TEXT,
    dui VARCHAR(20) UNIQUE            -- Documento de Identidad local
);

-- 6. Tabla de Estudiantes (Con validación para evitar duplicados de NIE)
CREATE TABLE IF NOT EXISTS estudiantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nie VARCHAR(20) UNIQUE NOT NULL,   -- Número de Identificación del Estudiante
    nombres VARCHAR(150) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    direccion TEXT,
    alergias_condiciones TEXT,
    encargado_id INT NOT NULL,
    grado_seccion_id INT NOT NULL,
    FOREIGN KEY (encargado_id) REFERENCES encargados(id) ON DELETE RESTRICT,
    FOREIGN KEY (grado_seccion_id) REFERENCES grados_secciones(id) ON DELETE RESTRICT,
    -- Restricción clave para evitar que el mismo estudiante (mismo NIE) se inscriba dos veces en el mismo año/grado
    UNIQUE KEY uk_estudiante_inscripcion (nie, grado_seccion_id)
);

-- 7. Tabla de Materias / Asignaturas
CREATE TABLE IF NOT EXISTS materias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre_materia VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- 8. Tabla de Carga Académica (Asignación de profesores a materias y secciones)
CREATE TABLE IF NOT EXISTS cargas_academicas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    profesor_id INT NOT NULL,
    materia_id INT NOT NULL,
    grado_seccion_id INT NOT NULL,
    FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE,
    FOREIGN KEY (grado_seccion_id) REFERENCES grados_secciones(id) ON DELETE CASCADE
);

-- 9. Tabla de Horarios de Clase (Programación semanal)
-- Regla de Negocio: La sección permanece en su aula base (grados_secciones.aula_base_id).
-- Los docentes rotan. Si hay traslado eventual a laboratorio/taller, se usa aula_especial_id (nullable).
CREATE TABLE IF NOT EXISTS horarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grado_seccion_id INT NOT NULL,
    materia_id INT NOT NULL,
    profesor_id INT NOT NULL,
    dia_semana ENUM('Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    aula_especial_id INT NULL,                    -- Opcional (NULL = se imparte en el aula base)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (grado_seccion_id) REFERENCES grados_secciones(id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES asignaturas(id) ON DELETE CASCADE,
    FOREIGN KEY (profesor_id) REFERENCES profesores(id) ON DELETE CASCADE,
    FOREIGN KEY (aula_especial_id) REFERENCES aulas(id) ON DELETE SET NULL,

    -- Restricciones de integridad del negocio:
    -- A) Ningún docente puede tener dos clases en el mismo bloque horario y día
    UNIQUE KEY uk_docente_bloque_horario (profesor_id, dia_semana, hora_inicio, hora_fin),
    -- B) Ninguna sección puede recibir dos materias a la vez
    UNIQUE KEY uk_seccion_bloque_horario (grado_seccion_id, dia_semana, hora_inicio, hora_fin),
    -- C) Ninguna aula especial ocupada simultáneamente por dos secciones (los NULL no colisionan)
    UNIQUE KEY uk_aula_especial_bloque (aula_especial_id, dia_semana, hora_inicio, hora_fin)
);

-- 10. Tabla de Asistencia Diaria (Control móvil por docentes)
CREATE TABLE IF NOT EXISTS asistencias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    grado_seccion_id INT NOT NULL,
    fecha DATE NOT NULL,
    estado ENUM('Presente', 'Ausente', 'Permiso') NOT NULL,
    observacion VARCHAR(255),
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
    FOREIGN KEY (grado_seccion_id) REFERENCES grados_secciones(id) ON DELETE CASCADE,
    UNIQUE KEY uk_asistencia_diaria (estudiante_id, fecha)
);

-- 11. Tabla de Calificaciones (Actividades y Exámenes - Escala 0.0 a 10.0)
CREATE TABLE IF NOT EXISTS calificaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    estudiante_id INT NOT NULL,
    materia_id INT NOT NULL,
    periodo ENUM('Trimestre 1', 'Trimestre 2', 'Trimestre 3') NOT NULL,
    nombre_actividad VARCHAR(150) NOT NULL,
    nota DECIMAL(4,2) CHECK (nota >= 0.0 AND nota <= 10.0),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE CASCADE,
    FOREIGN KEY (materia_id) REFERENCES materias(id) ON DELETE CASCADE
);

-- 12. Tabla de Cierres de Periodo (Para bloquear modificaciones no autorizadas)
CREATE TABLE IF NOT EXISTS cierres_periodos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo ENUM('Trimestre 1', 'Trimestre 2', 'Trimestre 3') UNIQUE NOT NULL,
    cerrado BOOLEAN DEFAULT FALSE,
    fecha_cierre TIMESTAMP NULL
);