import os
import sys
import random
from datetime import date, timedelta

# Soporte dual para MySQLdb (mysqlclient) o pymysql
try:
    import MySQLdb as mysql_driver
except ImportError:
    try:
        import pymysql as mysql_driver
    except ImportError:
        raise RuntimeError("No se encontró ningún controlador MySQL (MySQLdb ni pymysql)")

def run():
    print("==========================================================")
    print("   VACIADO E INYECCIÓN CON ROTACIÓN DOCENTE: SANTA SOFÍA  ")
    print("==========================================================")

    # Conectar a MySQL en localhost
    try:
        conn = mysql_driver.connect(
            host='127.0.0.1',
            user='root',
            passwd='',
            db='control_escolar_db',
            charset='utf8mb4'
        )
    except Exception:
        conn = mysql_driver.connect(
            host='127.0.0.1',
            user='root',
            password='',
            database='control_escolar_db',
            charset='utf8mb4'
        )
    
    cursor = conn.cursor()

    # 1. Limpieza de tablas
    print("\n[1/7] Vaciando tablas existentes...")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = [
        "calificaciones", "actividades_evaluativas", "asistencias",
        "horarios", "cargas_academicas", "estudiantes", "estudiante",
        "asignaturas", "grados_secciones", "aulas", "materias",
        "profesores", "usuarios", "periodos_escolares", "anios_lectivos",
        "cierres_periodos", "institucion_config"
    ]
    for t in tables:
        try:
            cursor.execute(f"TRUNCATE TABLE {t};")
        except Exception:
            cursor.execute(f"DELETE FROM {t};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    conn.commit()
    print(" -> Tablas vaciadas correctamente.")

    # 2. Institución y Configuración
    print("\n[2/7] Inyectando Configuración Institucional 'Complejo Educativo Santa Sofía'...")
    cursor.execute("""
        INSERT INTO institucion_config (id, nombre, codigo_mined, anio_lectivo, regimen, director_nombre, telefono, direccion)
        VALUES (1, 'Complejo Educativo Santa Sofía', '10234', '2026', 'Régimen Trimestral', 'Lic. Roberto Antonio Mendoza', '2222-3333', 'Barrio El Centro, San Salvador, El Salvador');
    """)

    # Año Lectivo 2026
    cursor.execute("""
        INSERT INTO anios_lectivos (id, anio, estado, descripcion)
        VALUES (1, '2026', 'Activo', 'Año Lectivo Regular 2026');
    """)

    # Períodos Trimestrales 2026
    cursor.execute("""
        INSERT INTO periodos_escolares (id, nombre, anio_lectivo_id, estado) VALUES
        (1, 'Trimestre 1 - 2026', 1, 'Abierto'),
        (2, 'Trimestre 2 - 2026', 1, 'Abierto'),
        (3, 'Trimestre 3 - 2026', 1, 'Cerrado');
    """)
    conn.commit()
    print(" -> Institución, Año Lectivo 2026 y Trimestres configurados.")

    # 3. Aulas Institucionales
    print("\n[3/7] Inyectando 21 Aulas (18 de Grado + 3 Especiales)...")
    aulas_data = [
        ("AUL-101", "Aula 1 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-102", "Aula 2 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-103", "Aula 3 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-104", "Aula 4 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-105", "Aula 5 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-106", "Aula 6 - Pabellón A", "Estandar", 30, "Pabellón A"),
        ("AUL-201", "Aula 7 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-202", "Aula 8 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-203", "Aula 9 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-204", "Aula 10 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-205", "Aula 11 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-206", "Aula 12 - Pabellón B", "Estandar", 30, "Pabellón B"),
        ("AUL-301", "Aula 13 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-302", "Aula 14 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-303", "Aula 15 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-304", "Aula 16 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-305", "Aula 17 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-306", "Aula 18 - Pabellón C", "Estandar", 30, "Pabellón C"),
        ("AUL-COMP", "Laboratorio de Cómputo", "Laboratorio", 40, "Edificio Central"),
        ("AUL-CIEN", "Laboratorio de Ciencias", "Laboratorio", 40, "Pabellón de Ciencias"),
        ("AUL-DEP", "Cancha Multiusos", "Cancha", 100, "Área Deportiva"),
    ]

    aula_id_map = {}
    for codigo, nombre, tipo, capacidad, ubicacion in aulas_data:
        cursor.execute("""
            INSERT INTO aulas (codigo, nombre, tipo, capacidad, ubicacion, estado)
            VALUES (%s, %s, %s, %s, %s, 1);
        """, (codigo, nombre, tipo, capacidad, ubicacion))
        aula_id_map[codigo] = cursor.lastrowid

    # 4. Grados y Secciones vinculadas a su aula_base_id
    print("\n[4/7] Inyectando Grados y Secciones vinculados a su Aula Base...")
    grados_secciones_def = [
        ("1º Grado", "Sección A", "AUL-101"),
        ("1º Grado", "Sección B", "AUL-102"),
        ("2º Grado", "Sección A", "AUL-103"),
        ("2º Grado", "Sección B", "AUL-104"),
        ("3º Grado", "Sección A", "AUL-105"),
        ("3º Grado", "Sección B", "AUL-106"),
        ("4º Grado", "Sección A", "AUL-201"),
        ("4º Grado", "Sección B", "AUL-202"),
        ("5º Grado", "Sección A", "AUL-203"),
        ("5º Grado", "Sección B", "AUL-204"),
        ("6º Grado", "Sección A", "AUL-205"),
        ("6º Grado", "Sección B", "AUL-206"),
        ("7º Grado", "Sección A", "AUL-301"),
        ("7º Grado", "Sección B", "AUL-302"),
        ("8º Grado", "Sección A", "AUL-303"),
        ("8º Grado", "Sección B", "AUL-304"),
        ("9º Grado", "Sección A", "AUL-305"),
        ("9º Grado", "Sección B", "AUL-306"),
    ]

    seccion_id_map = {}
    for grado, seccion, cod_aula in grados_secciones_def:
        aula_id = aula_id_map[cod_aula]
        cursor.execute("""
            INSERT INTO grados_secciones (grado, seccion, anio_lectivo, aula_base_id)
            VALUES (%s, %s, 2026, %s);
        """, (grado, seccion, aula_id))
        key = f"{grado} - {seccion}"
        seccion_id_map[key] = cursor.lastrowid

    # 5. Catálogo de Materias
    print("\n[5/7] Inyectando Catálogo de Materias y Planta Docente Especializada...")
    materias_data = [
        ("Matemáticas", "Álgebra, geometría, aritmética y cálculo aplicado"),
        ("Lenguaje y Literatura", "Lectura comprensiva, gramática y redacción"),
        ("Ciencias Naturales", "Biología, física, química y ecología"),
        ("Estudios Sociales", "Historia de El Salvador, geografía y sociedad"),
        ("Educación Física", "Deportes, acondicionamiento físico y salud"),
        ("Moral y Cívica", "Formación ciudadana, valores y ética"),
        ("Ortografía y Caligrafía", "Escritura correcta, trazo y motricidad fina"),
        ("Inglés", "Comprensión lectora, gramática y conversación"),
        ("Informática y Robótica", "Computación básica, ofimática y programación"),
        ("Educación Artística", "Expresión plástica, dibujo, música y arte"),
    ]

    materia_id_map = {}
    for nombre, desc in materias_data:
        cursor.execute("INSERT INTO materias (nombre_materia, descripcion) VALUES (%s, %s);", (nombre, desc))
        materia_id_map[nombre] = cursor.lastrowid

    # Planta Docente Completa y Especializada (18 Docentes para cubrir los 18 grupos simultáneos sin colisión)
    # Cada docente tiene su especialidad principal
    planta_docente = [
        # Especialistas Tercer Ciclo (7°, 8°, 9°)
        ("Carlos Alberto Morales", "carlos.docente@santasofia.edu.sv", "7890-1122", "Matemáticas"),
        ("María Elena Vásquez", "maria.docente@santasofia.edu.sv", "7890-2233", "Lenguaje y Literatura"),
        ("José Manuel Rivas", "jose.docente@santasofia.edu.sv", "7890-3344", "Ciencias Naturales"),
        ("Ana Patricia Gómez", "ana.docente@santasofia.edu.sv", "7890-4455", "Estudios Sociales"),
        ("Roberto Alexander Peña", "roberto.docente@santasofia.edu.sv", "7890-5566", "Educación Física"),
        ("Jorge Alberto Castillo", "jorge.docente@santasofia.edu.sv", "7890-6677", "Informática y Robótica"),
        ("Claudia Beatriz Flores", "claudia.docente@santasofia.edu.sv", "7890-7788", "Moral y Cívica"),
        ("Luis Fernando Hernández", "luis.docente@santasofia.edu.sv", "7890-8899", "Inglés"),

        # Especialistas Básica II Ciclo (4°, 5°, 6°)
        ("Silvia Marlene Rivas", "silvia.docente@santasofia.edu.sv", "7890-1133", "Matemáticas"),
        ("Nelson Ovidio Cruz", "nelson.docente@santasofia.edu.sv", "7890-2244", "Lenguaje y Literatura"),
        ("Karla Vanesa Ramos", "karla.docente@santasofia.edu.sv", "7890-3355", "Ciencias Naturales"),
        ("Héctor David Mendoza", "hector.docente@santasofia.edu.sv", "7890-4466", "Estudios Sociales"),
        ("Fátima Beatriz Portillo", "fatima.docente@santasofia.edu.sv", "7890-5577", "Educación Física"),
        ("Roxana Beatriz Pineda", "roxana.docente@santasofia.edu.sv", "7890-6688", "Inglés"),

        # Especialistas Básica I Ciclo (1°, 2°, 3°)
        ("Sofía Isabel Martínez", "sofia.docente@santasofia.edu.sv", "7890-7799", "Ortografía y Caligrafía"),
        ("Walter Antonio Mejía", "walter.docente@santasofia.edu.sv", "7890-8800", "Moral y Cívica"),
        ("Gabriela Elizabeth Amaya", "gabriela.docente@santasofia.edu.sv", "7890-9911", "Educación Artística"),
        ("Patricia Iveth Guardado", "patricia.docente@santasofia.edu.sv", "7890-9922", "Lenguaje y Literatura"),
    ]

    usuarios_data = [
        ("Lic. Roberto Antonio Mendoza", "director@santasofia.edu.sv", "admin123", "Director"),
        ("Sra. Carmen Elena Guardado", "secretaria@santasofia.edu.sv", "secretaria123", "Secretaria"),
    ]
    for nom, cor, tel, esp in planta_docente:
        usuarios_data.append((nom, cor, "docente123", "Profesor"))

    usuario_id_map = {}
    for nombre, correo, pwd, rol in usuarios_data:
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, password_hash, rol, estado)
            VALUES (%s, %s, %s, %s, 1);
        """, (nombre, correo, pwd, rol))
        usuario_id_map[correo] = cursor.lastrowid

    # Insertar en tabla 'profesores'
    docente_id_by_name = {}
    for nom, correo, tel, esp in planta_docente:
        uid = usuario_id_map[correo]
        cursor.execute("""
            INSERT INTO profesores (usuario_id, telefono, especialidad)
            VALUES (%s, %s, %s);
        """, (uid, tel, esp))
        prof_id = cursor.lastrowid
        docente_id_by_name[nom] = prof_id

    print(f" -> Creados {len(planta_docente)} docentes especializados.")

    # 6. Carga Académica (`asignaturas`)
    print("\n[6/7] Inyectando Asignaturas distribuidas a sus docentes titulares...")
    asignatura_id_map = {}
    
    prefijos = {
        "Matemáticas": "MAT",
        "Lenguaje y Literatura": "LEN",
        "Ciencias Naturales": "CIE",
        "Estudios Sociales": "SOC",
        "Educación Física": "EDF",
        "Moral y Cívica": "MOR",
        "Ortografía y Caligrafía": "ORT",
        "Inglés": "ING",
        "Informática y Robótica": "INF",
        "Educación Artística": "ART",
    }

    # Distribución de materias por sección y ciclo:
    # Tercer Ciclo (7° a 9°)
    secciones_tc = [
        ("7º Grado - Sección A", "7A"), ("7º Grado - Sección B", "7B"),
        ("8º Grado - Sección A", "8A"), ("8º Grado - Sección B", "8B"),
        ("9º Grado - Sección A", "9A"), ("9º Grado - Sección B", "9B"),
    ]
    docentes_tc_materia = {
        "Matemáticas": "Carlos Alberto Morales",
        "Lenguaje y Literatura": "María Elena Vásquez",
        "Ciencias Naturales": "José Manuel Rivas",
        "Estudios Sociales": "Ana Patricia Gómez",
        "Educación Física": "Roberto Alexander Peña",
        "Informática y Robótica": "Jorge Alberto Castillo",
        "Moral y Cívica": "Claudia Beatriz Flores",
        "Inglés": "Luis Fernando Hernández",
    }

    for gs, suf in secciones_tc:
        for mat, prof_nom in docentes_tc_materia.items():
            cod = f"{prefijos[mat]}-{suf}"
            cursor.execute("""
                INSERT INTO asignaturas (nombre, codigo, descripcion, grado_seccion, profesor_nombre)
                VALUES (%s, %s, %s, %s, %s);
            """, (mat, cod, f"{mat} ({gs})", gs, prof_nom))
            asignatura_id_map[(gs, mat)] = (cursor.lastrowid, prof_nom)
            cursor.execute("""
                INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id)
                VALUES (%s, %s, %s);
            """, (docente_id_by_name[prof_nom], materia_id_map[mat], seccion_id_map[gs]))

    # Básica II Ciclo (4° a 6°)
    secciones_b2 = [
        ("4º Grado - Sección A", "4A"), ("4º Grado - Sección B", "4B"),
        ("5º Grado - Sección A", "5A"), ("5º Grado - Sección B", "5B"),
        ("6º Grado - Sección A", "6A"), ("6º Grado - Sección B", "6B"),
    ]
    docentes_b2_materia = {
        "Matemáticas": "Silvia Marlene Rivas",
        "Lenguaje y Literatura": "Nelson Ovidio Cruz",
        "Ciencias Naturales": "Karla Vanesa Ramos",
        "Estudios Sociales": "Héctor David Mendoza",
        "Educación Física": "Fátima Beatriz Portillo",
        "Inglés": "Roxana Beatriz Pineda",
    }

    for gs, suf in secciones_b2:
        for mat, prof_nom in docentes_b2_materia.items():
            cod = f"{prefijos[mat]}-{suf}"
            cursor.execute("""
                INSERT INTO asignaturas (nombre, codigo, descripcion, grado_seccion, profesor_nombre)
                VALUES (%s, %s, %s, %s, %s);
            """, (mat, cod, f"{mat} ({gs})", gs, prof_nom))
            asignatura_id_map[(gs, mat)] = (cursor.lastrowid, prof_nom)
            cursor.execute("""
                INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id)
                VALUES (%s, %s, %s);
            """, (docente_id_by_name[prof_nom], materia_id_map[mat], seccion_id_map[gs]))

    # Básica I Ciclo (1° a 3°)
    secciones_b1 = [
        ("1º Grado - Sección A", "1A"), ("1º Grado - Sección B", "1B"),
        ("2º Grado - Sección A", "2A"), ("2º Grado - Sección B", "2B"),
        ("3º Grado - Sección A", "3A"), ("3º Grado - Sección B", "3B"),
    ]
    docentes_b1_materia = {
        "Ortografía y Caligrafía": "Sofía Isabel Martínez",
        "Moral y Cívica": "Walter Antonio Mejía",
        "Educación Artística": "Gabriela Elizabeth Amaya",
        "Lenguaje y Literatura": "Patricia Iveth Guardado",
        "Inglés": "Luis Fernando Hernández",
        "Matemáticas": "Claudia Beatriz Flores",
    }

    for gs, suf in secciones_b1:
        for mat, prof_nom in docentes_b1_materia.items():
            cod = f"{prefijos[mat]}-{suf}"
            cursor.execute("""
                INSERT INTO asignaturas (nombre, codigo, descripcion, grado_seccion, profesor_nombre)
                VALUES (%s, %s, %s, %s, %s);
            """, (mat, cod, f"{mat} ({gs})", gs, prof_nom))
            asignatura_id_map[(gs, mat)] = (cursor.lastrowid, prof_nom)
            cursor.execute("""
                INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id)
                VALUES (%s, %s, %s);
            """, (docente_id_by_name[prof_nom], materia_id_map[mat], seccion_id_map[gs]))

    print(f" -> Creadas {len(asignatura_id_map)} asignaturas en la carga académica.")

    # 7. Horarios Semanales con ROTACIÓN COMPLETA
    print("\n[7/7] Inyectando Horarios de Clase con Rotación Docente (Lunes a Viernes)...")
    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    bloques_horarios = [
        ("07:00:00", "08:30:00"),  # Bloque 1
        ("08:30:00", "09:15:00"),  # Bloque 2
        # (09:15 - 09:45 RECREO)
        ("09:45:00", "11:15:00"),  # Bloque 3
        ("11:15:00", "12:00:00"),  # Bloque 4
        # (12:00 - 12:30 RECREO)
        ("12:30:00", "14:00:00"),  # Bloque 5
    ]

    aula_dep_id = aula_id_map["AUL-DEP"]
    aula_comp_id = aula_id_map["AUL-COMP"]
    aula_cien_id = aula_id_map["AUL-CIEN"]

    # Definir la lista de rotación para Tercer Ciclo (6 materias, 6 docentes especialistas)
    # (Materia, Especialista, Aula Especial)
    tc_rotation_items = [
        ("Matemáticas", "Carlos Alberto Morales", None),
        ("Lenguaje y Literatura", "María Elena Vásquez", None),
        ("Ciencias Naturales", "José Manuel Rivas", None),
        ("Estudios Sociales", "Ana Patricia Gómez", None),
        ("Educación Física", "Roberto Alexander Peña", aula_dep_id),
        ("Informática y Robótica", "Jorge Alberto Castillo", aula_comp_id),
    ]

    # Básica II Ciclo (6 materias, 6 docentes especialistas)
    b2_rotation_items = [
        ("Matemáticas", "Silvia Marlene Rivas", None),
        ("Lenguaje y Literatura", "Nelson Ovidio Cruz", None),
        ("Ciencias Naturales", "Karla Vanesa Ramos", None),
        ("Estudios Sociales", "Héctor David Mendoza", None),
        ("Educación Física", "Fátima Beatriz Portillo", None), # Cancha la usa TC en este turno
        ("Inglés", "Roxana Beatriz Pineda", None),
    ]

    # Básica I Ciclo (6 materias, 6 docentes especialistas, 4 bloques)
    b1_rotation_items = [
        ("Ortografía y Caligrafía", "Sofía Isabel Martínez", None),
        ("Moral y Cívica", "Walter Antonio Mejía", None),
        ("Educación Artística", "Gabriela Elizabeth Amaya", None),
        ("Lenguaje y Literatura", "Patricia Iveth Guardado", None),
        ("Inglés", "Luis Fernando Hernández", None),
        ("Matemáticas", "Claudia Beatriz Flores", None),
    ]

    tc_keys = [s[0] for s in secciones_tc]
    b2_keys = [s[0] for s in secciones_b2]
    b1_keys = [s[0] for s in secciones_b1]

    horarios_totales = 0

    for d_idx, dia in enumerate(dias_semana):
        for b_idx, (b_start, b_end) in enumerate(bloques_horarios):
            
            # --- ROTACIÓN TERCER CICLO (7°, 8°, 9°) ---
            # Desplazamiento rotativo estricto: en cada bloque cada maestro atiende un grupo diferente
            offset_tc = (d_idx * 3 + b_idx) % 6
            for s_idx, gs in enumerate(tc_keys):
                mat_nom, prof_nom, aula_esp = tc_rotation_items[(s_idx + offset_tc) % 6]
                sec_id = seccion_id_map[gs]
                prof_id = docente_id_by_name[prof_nom]
                asig_id, _ = asignatura_id_map[(gs, mat_nom)]

                # Asignar aula de ciencias los viernes para práctica
                aula_final = aula_esp
                if mat_nom == "Ciencias Naturales" and dia == "Viernes" and b_idx == 0 and s_idx == 0:
                    aula_final = aula_cien_id

                cursor.execute("""
                    INSERT INTO horarios (grado_seccion_id, materia_id, profesor_id, anio_lectivo_id, dia_semana, hora_inicio, hora_fin, aula_especial_id)
                    VALUES (%s, %s, %s, 1, %s, %s, %s, %s);
                """, (sec_id, asig_id, prof_id, dia, b_start, b_end, aula_final))
                horarios_totales += 1

            # --- ROTACIÓN BÁSICA II CICLO (4°, 5°, 6°) ---
            offset_b2 = (d_idx * 2 + b_idx) % 6
            for s_idx, gs in enumerate(b2_keys):
                mat_nom, prof_nom, aula_esp = b2_rotation_items[(s_idx + offset_b2) % 6]
                sec_id = seccion_id_map[gs]
                prof_id = docente_id_by_name[prof_nom]
                asig_id, _ = asignatura_id_map[(gs, mat_nom)]

                cursor.execute("""
                    INSERT INTO horarios (grado_seccion_id, materia_id, profesor_id, anio_lectivo_id, dia_semana, hora_inicio, hora_fin, aula_especial_id)
                    VALUES (%s, %s, %s, 1, %s, %s, %s, %s);
                """, (sec_id, asig_id, prof_id, dia, b_start, b_end, aula_esp))
                horarios_totales += 1

            # --- ROTACIÓN BÁSICA I CICLO (1°, 2°, 3°) ---
            # 1° a 3° salen a las 12:45 / 4 bloques matutinos
            if b_idx < 4:
                offset_b1 = (d_idx * 4 + b_idx) % 6
                for s_idx, gs in enumerate(b1_keys):
                    mat_nom, prof_nom, aula_esp = b1_rotation_items[(s_idx + offset_b1) % 6]
                    sec_id = seccion_id_map[gs]
                    prof_id = docente_id_by_name[prof_nom]
                    asig_id, _ = asignatura_id_map[(gs, mat_nom)]

                    cursor.execute("""
                        INSERT INTO horarios (grado_seccion_id, materia_id, profesor_id, anio_lectivo_id, dia_semana, hora_inicio, hora_fin, aula_especial_id)
                        VALUES (%s, %s, %s, 1, %s, %s, %s, %s);
                    """, (sec_id, asig_id, prof_id, dia, b_start, b_end, aula_esp))
                    horarios_totales += 1

    print(f" -> Insertados {horarios_totales} bloques horarios sin colisiones con rotación completa.")

    # 8. Actividades Evaluativas para Carlos Alberto Morales en MAT-7A
    asig_mat7a, _ = asignatura_id_map[("7º Grado - Sección A", "Matemáticas")]
    actividades_prueba = [
        (asig_mat7a, 1, "Examen Parcial 1 (35%)", "Examen", 35.0, "2026-03-20", "Evaluación de Álgebra y Números Reales"),
        (asig_mat7a, 1, "Guía #1: Ecuaciones Lineales (25%)", "Guía", 25.0, "2026-03-10", "Guía práctica de ejercicios en parejas"),
        (asig_mat7a, 1, "Tareas y Cuaderno (20%)", "Tarea", 20.0, "2026-03-25", "Revisión diaria de ejercicios y puntualidad"),
        (asig_mat7a, 1, "Laboratorio Aplicado (20%)", "Laboratorio", 20.0, "2026-03-28", "Resolución de problemas en equipo"),
    ]
    for asig_id, per_id, nom, tip, pond, fec, desc in actividades_prueba:
        cursor.execute("""
            INSERT INTO actividades_evaluativas (asignatura_id, periodo_id, nombre, tipo, ponderacion, fecha, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (asig_id, per_id, nom, tip, pond, fec, desc))

    # 9. Estudiantes, Calificaciones y Asistencias de Prueba
    print("\n[8/8] Inyectando Padrón de Estudiantes, Notas y Asistencias...")
    nombres_hombres = ["Kevin Alexander", "Mateo Alejandro", "Jonathan Josué", "Carlos Daniel", "Diego Fernando", "Rodrigo Antonio", "Gabriel Ernesto", "Emerson José"]
    nombres_mujeres = ["Sofía Valentina", "Valeria Nicole", "Camila Daniela", "Andrea Guadalupe", "Mariana Beatriz", "Fátima Elizabeth", "Lucía Fernanda", "Jimena Abigail"]
    apellidos = ["Alvarado Menjívar", "Gómez Hernández", "Flores Vásquez", "Castillo Ramos", "Rivas Portillo", "Pérez Quintanilla", "Rodríguez Cornejo", "Mejía Solórzano", "Aguilar Chicas", "Zelaya Lemus"]

    estudiantes_creados = []
    nie_counter = 1045001

    secciones_con_alumnos = [
        "1º Grado - Sección A",
        "1º Grado - Sección B",
        "2º Grado - Sección A",
        "3º Grado - Sección A",
        "4º Grado - Sección A",
        "5º Grado - Sección A",
        "6º Grado - Sección A",
        "7º Grado - Sección A",
        "7º Grado - Sección B",
        "8º Grado - Sección A",
        "9º Grado - Sección A",
    ]

    for gs in secciones_con_alumnos:
        for i in range(12):
            if i % 2 == 0:
                nom = f"{random.choice(nombres_hombres)} {random.choice(apellidos)}"
            else:
                nom = f"{random.choice(nombres_mujeres)} {random.choice(apellidos)}"
            nie = str(nie_counter)
            nie_counter += 1
            encargado = f"Responsable: {random.choice(nombres_mujeres)} {random.choice(apellidos)}"
            telefono = f"7{random.randint(100, 999)}-{random.randint(1000, 9999)}"

            cursor.execute("""
                INSERT INTO estudiantes (nie, nombre_completo, grado_seccion, encargado, telefono)
                VALUES (%s, %s, %s, %s, %s);
            """, (nie, nom, gs, encargado, telefono))
            est_id = cursor.lastrowid
            estudiantes_creados.append((est_id, nie, nom, gs))

    # Calificaciones de Muestra para 7º Grado - Sección A en MAT-7A
    estudiantes_7a = [e for e in estudiantes_creados if e[3] == "7º Grado - Sección A"]
    actividades_nombres = [
        "Examen Parcial 1 (35%)",
        "Guía #1: Ecuaciones Lineales (25%)",
        "Tareas y Cuaderno (20%)",
        "Laboratorio Aplicado (20%)"
    ]
    notas_distribucion = [8.5, 9.2, 7.8, 10.0, 6.5, 8.0, 9.5, 7.0, 8.8, 9.0, 6.0, 7.5]

    for idx, (est_id, nie, nom, gs) in enumerate(estudiantes_7a):
        base_nota = notas_distribucion[idx % len(notas_distribucion)]
        for act in actividades_nombres:
            nota_act = min(10.0, max(5.0, round(base_nota + random.uniform(-0.4, 0.4), 1)))
            cursor.execute("""
                INSERT INTO calificaciones (estudiante_id, asignatura_id, periodo_id, nota, tipo_evaluacion)
                VALUES (%s, %s, 1, %s, %s);
            """, (est_id, asig_mat7a, nota_act, act))

    # Calificaciones de Muestra para 1º Grado - Sección A
    estudiantes_1a = [e for e in estudiantes_creados if e[3] == "1º Grado - Sección A"]
    asig_mat1a, _ = asignatura_id_map[("1º Grado - Sección A", "Matemáticas")]
    asig_len1a, _ = asignatura_id_map[("1º Grado - Sección A", "Lenguaje y Literatura")]
    asig_ort1a, _ = asignatura_id_map[("1º Grado - Sección A", "Ortografía y Caligrafía")]

    for idx, (est_id, nie, nom, gs) in enumerate(estudiantes_1a):
        base_nota = notas_distribucion[idx % len(notas_distribucion)]
        cursor.execute("INSERT INTO calificaciones (estudiante_id, asignatura_id, periodo_id, nota, tipo_evaluacion) VALUES (%s, %s, 1, %s, 'Evaluación Trimestral');", (est_id, asig_mat1a, base_nota))
        cursor.execute("INSERT INTO calificaciones (estudiante_id, asignatura_id, periodo_id, nota, tipo_evaluacion) VALUES (%s, %s, 1, %s, 'Evaluación Trimestral');", (est_id, asig_len1a, min(10.0, base_nota + 0.3)))
        cursor.execute("INSERT INTO calificaciones (estudiante_id, asignatura_id, periodo_id, nota, tipo_evaluacion) VALUES (%s, %s, 1, %s, 'Evaluación Trimestral');", (est_id, asig_ort1a, min(10.0, base_nota + 0.5)))

    # Asistencias de la última semana escolar (5 días)
    hoy = date.today()
    dias_asistencia = []
    for d in range(1, 10):
        dia_eval = hoy - timedelta(days=d)
        if dia_eval.weekday() < 5:
            dias_asistencia.append(dia_eval)
        if len(dias_asistencia) == 5:
            break

    for est_id, nie, nom, gs in estudiantes_creados:
        for fecha_asist in dias_asistencia:
            rnd = random.random()
            if rnd < 0.88:
                estado_asist = "Presente"
            elif rnd < 0.95:
                estado_asist = "Tarde"
            else:
                estado_asist = "Ausente"
            cursor.execute("""
                INSERT INTO asistencias (estudiante_id, fecha, estado, observacion)
                VALUES (%s, %s, %s, %s);
            """, (est_id, fecha_asist, estado_asist, "Asistencia regular"))

    conn.commit()
    cursor.close()
    conn.close()
    print(" -> Inyección MySQL finalizada con éxito rotundo!")

    # 10. Sincronizar Django auth_user y PerfilUsuario
    print("\n[Sync] Sincronizando usuarios en Django...")
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend_web")))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_web.settings")
        import django
        django.setup()

        from django.contrib.auth.models import User
        from portal.models import PerfilUsuario, ConfiguracionInstitucion

        # Configuración Institucional
        inst = ConfiguracionInstitucion.get_activa()
        inst.nombre = "Complejo Educativo Santa Sofía"
        inst.codigo_mined = "10234"
        inst.director_nombre = "Lic. Roberto Antonio Mendoza"
        inst.direccion = "Barrio El Centro, San Salvador, El Salvador"
        inst.telefono = "2222-3333"
        inst.logo = "institucion/logo_santa_sofia.jpg"
        inst.save()

        # Sincronizar todos los usuarios
        for nombre, correo, pwd, rol in usuarios_data:
            dj_user, created = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
            dj_user.set_password(pwd)
            dj_user.first_name = nombre
            dj_user.save()
            PerfilUsuario.objects.update_or_create(user=dj_user, defaults={"rol": rol})
        print(f" -> {len(usuarios_data)} usuarios sincronizados en Django y listos para acceder.")

    except Exception as e:
        print(f" [Advertencia] Error sincronizando Django: {e}")

    print("\n==========================================================")
    print("   ¡PROCESO COMPLETADO! SISTEMA CON HORARIOS SURTIDOS     ")
    print("==========================================================")

if __name__ == "__main__":
    run()