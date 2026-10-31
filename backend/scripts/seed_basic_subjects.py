import pymysql
import random

def seed_basic_subjects():
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='control_escolar_db',
        charset='utf8mb4',
        autocommit=False
    )
    cursor = conn.cursor()

    # Profesores disponibles:
    # Sofía Isabel Martínez (1° a 3° Primaria)
    # Jorge Alberto Castillo (4° a 6° Primaria)
    # Luis Fernando Hernández (Inglés)
    # Roberto Alexander Peña (Educación Física)

    grados_basica = [
        ("1º Grado - Sección A", "1A", "Sofía Isabel Martínez"),
        ("1º Grado - Sección B", "1B", "Sofía Isabel Martínez"),
        ("2º Grado - Sección A", "2A", "Sofía Isabel Martínez"),
        ("2º Grado - Sección B", "2B", "Sofía Isabel Martínez"),
        ("3º Grado - Sección A", "3A", "Sofía Isabel Martínez"),
        ("3º Grado - Sección B", "3B", "Sofía Isabel Martínez"),
        ("4º Grado - Sección A", "4A", "Jorge Alberto Castillo"),
        ("4º Grado - Sección B", "4B", "Jorge Alberto Castillo"),
        ("5º Grado - Sección A", "5A", "Jorge Alberto Castillo"),
        ("5º Grado - Sección B", "5B", "Jorge Alberto Castillo"),
        ("6º Grado - Sección A", "6A", "Jorge Alberto Castillo"),
        ("6º Grado - Sección B", "6B", "Jorge Alberto Castillo"),
    ]

    materias_basica_nombres = [
        ("Matemática", "MAT"),
        ("Lenguaje (Lectura)", "LEN"),
        ("Ciencias Salud y Medio Ambiente", "CIE"),
        ("Estudios Sociales", "SOC"),
        ("Inglés", "ING"),
        ("Expresión Artística", "ART"),
        ("Ortografía y Caligrafía", "ORT"),
        ("Educación Física", "EDF"),
    ]

    nuevas_asignaturas = []
    for gs, suf, prof_base in grados_basica:
        for nom_mat, pref in materias_basica_nombres:
            cod = f"{pref}-{suf}"
            if pref == "ING":
                prof = "Luis Fernando Hernández"
            elif pref == "EDF":
                prof = "Roberto Alexander Peña"
            else:
                prof = prof_base

            # Verificar si ya existe
            cursor.execute("SELECT id FROM asignaturas WHERE codigo = %s;", (cod,))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO asignaturas (nombre, codigo, descripcion, grado_seccion, profesor_nombre)
                    VALUES (%s, %s, %s, %s, %s);
                """, (f"{nom_mat} — {gs.split(' - ')[0]} {gs[-1]}", cod, f"Plan Curricular 2026 - {gs}", gs, prof))
                asig_id = cursor.lastrowid
                nuevas_asignaturas.append((asig_id, cod, nom_mat, gs, prof))

    print(f" -> Insertadas {len(nuevas_asignaturas)} nuevas asignaturas para Primaria (1° a 6°).")

    # Inyectar Calificaciones de Muestra para 1º Grado - Sección A en Trimestre 1 - 2026
    cursor.execute("SELECT id, nombre_completo FROM estudiantes WHERE grado_seccion = '1º Grado - Sección A';")
    alumnos_1a = cursor.fetchall()

    cursor.execute("SELECT id, nombre, codigo FROM asignaturas WHERE grado_seccion = '1º Grado - Sección A';")
    asigs_1a = cursor.fetchall()

    actividades_1a = [
        "Examen Trimestral 1 (35%)",
        "Tareas y Guías de Lectura (35%)",
        "Participación y Caligrafía (30%)"
    ]

    notas_dist = [9.0, 8.5, 9.8, 7.5, 8.0, 10.0, 6.8, 9.2, 8.8, 7.2, 9.5, 8.3]

    califs_count = 0
    for idx, (est_id, nom_est) in enumerate(alumnos_1a):
        base_nota = notas_dist[idx % len(notas_dist)]
        for asig_id, asig_nom, asig_cod in asigs_1a:
            for act in actividades_1a:
                nota = min(10.0, max(5.0, round(base_nota + random.uniform(-0.6, 0.6), 1)))
                cursor.execute("""
                    INSERT INTO calificaciones (estudiante_id, asignatura_id, periodo_id, nota, tipo_evaluacion)
                    VALUES (%s, %s, 1, %s, %s);
                """, (est_id, asig_id, nota, act))
                califs_count += 1

    conn.commit()
    cursor.close()
    conn.close()
    print(f" -> Insertadas {califs_count} calificaciones para los 12 estudiantes de 1º Grado - Sección A.")

if __name__ == "__main__":
    seed_basic_subjects()
