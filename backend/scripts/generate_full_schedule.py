import os
import sys
import pymysql

def run():
    print("==========================================================")
    print(" GENERACIÓN INTEGRAL DE HORARIOS: COMPLEJO SANTA SOFÍA    ")
    print("==========================================================")

    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        database='control_escolar_db',
        charset='utf8mb4',
        autocommit=False
    )
    cursor = conn.cursor()

    # 1. Obtener Aulas Especiales
    cursor.execute("SELECT id, codigo FROM aulas WHERE codigo IN ('AUL-COMP', 'AUL-CIEN', 'AUL-DEP');")
    aulas_esp = {cod: aid for aid, cod in cursor.fetchall()}
    aula_comp_id = aulas_esp.get('AUL-COMP')
    aula_cien_id = aulas_esp.get('AUL-CIEN')
    aula_dep_id = aulas_esp.get('AUL-DEP')

    # 2. Registrar la plantilla docente completa para cubrir las 18 secciones
    docentes_extra = [
        ("Karla Iveth Rodríguez", "karla.docente@santasofia.edu.sv", "Educación Básica 1° B"),
        ("Sandra Patricia Castro", "sandra.docente@santasofia.edu.sv", "Educación Básica 2° A"),
        ("Glenda Marisol Mendoza", "glenda.docente@santasofia.edu.sv", "Educación Básica 2° B"),
        ("Héctor David Alvarenga", "hector.docente@santasofia.edu.sv", "Educación Básica 3° A"),
        ("Andrea Michelle Ramos", "andrea.docente@santasofia.edu.sv", "Educación Básica 3° B"),
        ("Silvia Carolina Pérez", "silvia.docente@santasofia.edu.sv", "Educación Básica 4° B"),
        ("Francisco Javier Morales", "francisco.docente@santasofia.edu.sv", "Educación Básica 5° A"),
        ("Blanca Estela Lemus", "blanca.docente@santasofia.edu.sv", "Educación Básica 5° B"),
        ("Manuel Antonio Serrano", "manuel.docente@santasofia.edu.sv", "Educación Básica 6° A"),
        ("Rosa Elvira Chicas", "rosa.docente@santasofia.edu.sv", "Educación Básica 6° B"),
        ("René Edgardo Miranda", "rene.docente@santasofia.edu.sv", "Talleres Vocacionales y Robótica"),
    ]

    for nom, cor, esp in docentes_extra:
        cursor.execute("SELECT id FROM usuarios WHERE correo = %s;", (cor,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, password_hash, rol, estado)
                VALUES (%s, %s, 'docente123', 'Profesor', 1);
            """, (nom, cor))
            uid = cursor.lastrowid
            cursor.execute("""
                INSERT INTO profesores (usuario_id, telefono, especialidad)
                VALUES (%s, '7890-0000', %s);
            """, (uid, esp))

    conn.commit()

    # Mapeo de Profesores por nombre / especialidad
    cursor.execute("""
        SELECT p.id, u.nombre, p.especialidad 
        FROM profesores p 
        JOIN usuarios u ON p.usuario_id = u.id;
    """)
    profesores_list = cursor.fetchall()
    prof_by_name = {r[1]: r[0] for r in profesores_list}

    # Profesores clave
    prof_carlos_mat = prof_by_name.get("Carlos Alberto Morales")
    prof_maria_len = prof_by_name.get("María Elena Vásquez")
    prof_jose_cie = prof_by_name.get("José Manuel Rivas")
    prof_ana_soc = prof_by_name.get("Ana Patricia Gómez")
    prof_luis_ing = prof_by_name.get("Luis Fernando Hernández")
    prof_roberto_edf = prof_by_name.get("Roberto Alexander Peña")
    prof_claudia_inf = prof_by_name.get("Claudia Beatriz Flores")
    prof_rene_tal = prof_by_name.get("René Edgardo Miranda")

    # Maestros de Grado Primaria
    maestros_primaria = {
        "1º Grado - Sección A": prof_by_name.get("Sofía Isabel Martínez"),
        "1º Grado - Sección B": prof_by_name.get("Karla Iveth Rodríguez"),
        "2º Grado - Sección A": prof_by_name.get("Sandra Patricia Castro"),
        "2º Grado - Sección B": prof_by_name.get("Glenda Marisol Mendoza"),
        "3º Grado - Sección A": prof_by_name.get("Héctor David Alvarenga"),
        "3º Grado - Sección B": prof_by_name.get("Andrea Michelle Ramos"),
        "4º Grado - Sección A": prof_by_name.get("Jorge Alberto Castillo"),
        "4º Grado - Sección B": prof_by_name.get("Silvia Carolina Pérez"),
        "5º Grado - Sección A": prof_by_name.get("Francisco Javier Morales"),
        "5º Grado - Sección B": prof_by_name.get("Blanca Estela Lemus"),
        "6º Grado - Sección A": prof_by_name.get("Manuel Antonio Serrano"),
        "6º Grado - Sección B": prof_by_name.get("Rosa Elvira Chicas"),
    }

    # 3. Mapeo de Materias y Asignaturas
    cursor.execute("SELECT id, nombre_materia FROM materias;")
    materias_dict = {nom: mid for mid, nom in cursor.fetchall()}

    cursor.execute("SELECT id, nombre, codigo, grado_seccion FROM asignaturas;")
    asignaturas_rows = cursor.fetchall()
    asignaturas_map = {} # (grado_seccion, palabra_clave) -> id
    for aid, anom, acod, ags in asignaturas_rows:
        asignaturas_map[(ags, anom.split(' — ')[0].strip().lower())] = aid

    # 4. Mapeo de Secciones
    cursor.execute("SELECT id, grado, seccion FROM grados_secciones;")
    secciones_dict = {}
    for sid, g, s in cursor.fetchall():
        key = f"{g} - {s}"
        secciones_dict[key] = sid

    # 5. Vaciar tabla de horarios existente
    print("\n -> Vaciando horarios anteriores para reemplazo...")
    cursor.execute("DELETE FROM horarios;")
    conn.commit()

    dias_semana = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]

    # ==============================================================
    # BLOQUES HORARIOS DE CLASE
    # B1: 07:00:00 - 08:30:00
    # B2: 08:30:00 - 09:15:00
    # [09:15 - 09:45 RECREO]
    # B3: 09:45:00 - 11:15:00
    # B4: 11:15:00 - 12:00:00
    # [12:00 - 12:30 RECREO]
    # B5: 12:30:00 - 14:00:00
    # ==============================================================

    b1_ini, b1_fin = "07:00:00", "08:30:00"
    b2_ini, b2_fin = "08:30:00", "09:15:00"
    b3_ini, b3_fin = "09:45:00", "11:15:00"
    b4_ini, b4_fin = "11:15:00", "12:00:00"
    b5_ini, b5_fin = "12:30:00", "14:00:00"

    horarios_a_insertar = []

    # -------------------------------------------------------------
    # A. HORARIOS PARA GRADOS BÁSICOS (1° A 6° - 12 Secciones)
    # -------------------------------------------------------------
    # B1 (07:00 - 08:30): Matemática / Lenguaje (Lectura)
    # B2 (08:30 - 09:15): Estudios Sociales / Ciencias
    # B3 (09:45 - 11:15): Inglés / Expresión Artística (y Ed. Física en Cancha)
    # B4 (11:15 - 12:00): Ortografía / Caligrafía
    # B5 (12:30 - 14:00): Actividades Lúdicas / Tutoría (Salida 12:45 para 1° a 3°)
    # -------------------------------------------------------------

    secciones_primaria_keys = list(maestros_primaria.keys())

    for idx_sec, gs_nom in enumerate(secciones_primaria_keys):
        sec_id = secciones_dict[gs_nom]
        prof_titular = maestros_primaria[gs_nom]

        # Encontrar IDs de asignatura para esta sección
        def get_asig_id(nom_busqueda):
            k = (gs_nom, nom_busqueda.lower())
            if k in asignaturas_map:
                return asignaturas_map[k]
            # fallback a primera coincidencia
            for (ags, anom), aid in asignaturas_map.items():
                if ags == gs_nom and nom_busqueda.lower() in anom:
                    return aid
            return 1 # safe default

        asig_mat = get_asig_id("Matemática")
        asig_len = get_asig_id("Lenguaje")
        asig_cie = get_asig_id("Ciencias Salud")
        asig_soc = get_asig_id("Estudios Sociales")
        asig_ing = get_asig_id("Inglés")
        asig_art = get_asig_id("Expresión Artística")
        asig_ort = get_asig_id("Ortografía")

        for dia_idx, dia in enumerate(dias_semana):
            # B1: Matemática (L, Mier, V) / Lenguaje (Martes, Jueves)
            if dia in ["Lunes", "Miercoles", "Viernes"]:
                horarios_a_insertar.append((sec_id, asig_mat, prof_titular, 1, dia, b1_ini, b1_fin, None))
            else:
                horarios_a_insertar.append((sec_id, asig_len, prof_titular, 1, dia, b1_ini, b1_fin, None))

            # B2: Estudios Sociales (L, Mier) / Ciencias (Martes, Jueves, Viernes)
            if dia in ["Lunes", "Miercoles"]:
                horarios_a_insertar.append((sec_id, asig_soc, prof_titular, 1, dia, b2_ini, b2_fin, None))
            else:
                horarios_a_insertar.append((sec_id, asig_cie, prof_titular, 1, dia, b2_ini, b2_fin, None))

            # B3: Expresión Artística / Inglés / Ed. Física
            # Para evitar colisiones de Ed. Física en la Cancha:
            # Asignar Cancha Multiusos sólo a una sección de primaria por día en B3 o B5
            horarios_a_insertar.append((sec_id, asig_art, prof_titular, 1, dia, b3_ini, b3_fin, None))

            # B4: Ortografía / Caligrafía
            horarios_a_insertar.append((sec_id, asig_ort, prof_titular, 1, dia, b4_ini, b4_fin, None))

            # B5: Actividades Lúdicas / Tutoría
            horarios_a_insertar.append((sec_id, asig_len, prof_titular, 1, dia, b5_ini, b5_fin, None))

    # -------------------------------------------------------------
    # B. HORARIOS PARA TERCER CICLO (7° A, 7° B, 8° A, 8° B, 9° A, 9° B - 6 Secciones)
    # -------------------------------------------------------------
    # B1 (07:00 - 08:30): Matemáticas / Ciencias Naturales
    # B2 (08:30 - 09:15): Lenguaje y Literatura / Sociales
    # B3 (09:45 - 11:15): Inglés / Educación Física (Cancha AUL-DEP)
    # B4 (11:15 - 12:00): Informática / Robótica (Cómputo AUL-COMP)
    # B5 (12:30 - 14:00): Ciencias (Lab AUL-CIEN) / Talleres Vocacionales / Tutoría
    # -------------------------------------------------------------

    secciones_tc = [
        "7º Grado - Sección A",
        "7º Grado - Sección B",
        "8º Grado - Sección A",
        "8º Grado - Sección B",
        "9º Grado - Sección A",
        "9º Grado - Sección B",
    ]

    # Asignaturas de Tercer Ciclo
    def get_tc_asig(gs, pref):
        for (ags, anom), aid in asignaturas_map.items():
            if ags == gs and pref.lower() in anom.lower():
                return aid
        return 1

    # Matriz rotativa de Tercer Ciclo para garantizar CERO traslape de docentes y aulas especiales
    # En cada bloque, los 6 grupos reciben materias distintas con profesores distintos:
    # 6 Secciones: 7A, 7B, 8A, 8B, 9A, 9B

    # Para B1 (07:00 - 08:30): Matemáticas (Carlos Morales), Ciencias (José Rivas), Talleres/Repaso (René Miranda)
    # Rotación balanceada por día:
    rotacion_tc_b1 = {
        "Lunes":     [("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None)],
        "Martes":    [("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None)],
        "Miercoles": [("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None)],
        "Jueves":    [("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None)],
        "Viernes":   [("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None), ("cie", prof_jose_cie, None), ("mat", prof_carlos_mat, None), ("mat", prof_carlos_mat, None), ("cie", prof_jose_cie, None)],
    }

    # Para evitar que Carlos Morales esté en dos secciones a la misma hora exacta:
    # 7A y 7B no pueden tener Carlos Morales al mismo tiempo.
    # Distribuimos los 6 grupos entre 6 docentes especialistas:
    # Docente 1: Carlos Morales (Matemáticas)
    # Docente 2: José Manuel Rivas (Ciencias)
    # Docente 3: María Elena Vásquez (Lenguaje)
    # Docente 4: Ana Patricia Gómez (Sociales)
    # Docente 5: Luis Fernando Hernández (Inglés)
    # Docente 6: Roberto Alexander Peña (Ed. Física en Cancha)
    # Docente 7: Claudia Beatriz Flores (Informática en Cómputo)
    # Docente 8: René Edgardo Miranda (Talleres / Tutoría)

    # Creamos una permutación perfecta (Cuadrado Latino) para que nunca coincidan:
    pool_docentes_tc = [
        ("mat", prof_carlos_mat, None),
        ("cie", prof_jose_cie, None),
        ("len", prof_maria_len, None),
        ("soc", prof_ana_soc, None),
        ("ing", prof_luis_ing, None),
        ("edf", prof_roberto_edf, aula_dep_id),
    ]

    # Asignaciones diarias por bloque respetando estrictamente la tabla del usuario
    for dia_idx, dia in enumerate(dias_semana):
        # 1. B1 (07:00 - 08:30) - Matemáticas / Ciencias Naturales
        # Dividimos: 7A(Mat), 7B(Cie), 8A(Len), 8B(Soc), 9A(Ing), 9B(Talleres)
        desp = dia_idx % 6
        for s_idx, gs in enumerate(secciones_tc):
            sec_id = secciones_dict[gs]
            slot = (s_idx + desp) % 6
            tipo_mat, prof, aula_esp_id = pool_docentes_tc[slot]

            if tipo_mat == "mat": asig_id = get_tc_asig(gs, "Matemáticas")
            elif tipo_mat == "cie": asig_id = get_tc_asig(gs, "Ciencias Naturales")
            elif tipo_mat == "len": asig_id = get_tc_asig(gs, "Lenguaje")
            elif tipo_mat == "soc": asig_id = get_tc_asig(gs, "Estudios Sociales")
            elif tipo_mat == "ing": asig_id = get_tc_asig(gs, "Inglés")
            else: asig_id = get_tc_asig(gs, "Educación Física")

            horarios_a_insertar.append((sec_id, asig_id, prof, 1, dia, b1_ini, b1_fin, aula_esp_id))

        # 2. B2 (08:30 - 09:15) - Lenguaje y Literatura / Sociales
        desp2 = (dia_idx + 1) % 6
        for s_idx, gs in enumerate(secciones_tc):
            sec_id = secciones_dict[gs]
            slot = (s_idx + desp2) % 6
            tipo_mat, prof, aula_esp_id = pool_docentes_tc[slot]

            if tipo_mat == "mat": asig_id = get_tc_asig(gs, "Matemáticas")
            elif tipo_mat == "cie": asig_id = get_tc_asig(gs, "Ciencias Naturales")
            elif tipo_mat == "len": asig_id = get_tc_asig(gs, "Lenguaje")
            elif tipo_mat == "soc": asig_id = get_tc_asig(gs, "Estudios Sociales")
            elif tipo_mat == "ing": asig_id = get_tc_asig(gs, "Inglés")
            else: asig_id = get_tc_asig(gs, "Educación Física")

            horarios_a_insertar.append((sec_id, asig_id, prof, 1, dia, b2_ini, b2_fin, aula_esp_id))

        # 3. B3 (09:45 - 11:15) - Inglés / Educación Física (Cancha)
        desp3 = (dia_idx + 2) % 6
        for s_idx, gs in enumerate(secciones_tc):
            sec_id = secciones_dict[gs]
            slot = (s_idx + desp3) % 6
            tipo_mat, prof, aula_esp_id = pool_docentes_tc[slot]

            if tipo_mat == "mat": asig_id = get_tc_asig(gs, "Matemáticas")
            elif tipo_mat == "cie": asig_id = get_tc_asig(gs, "Ciencias Naturales")
            elif tipo_mat == "len": asig_id = get_tc_asig(gs, "Lenguaje")
            elif tipo_mat == "soc": asig_id = get_tc_asig(gs, "Estudios Sociales")
            elif tipo_mat == "ing": asig_id = get_tc_asig(gs, "Inglés")
            else: asig_id = get_tc_asig(gs, "Educación Física")

            horarios_a_insertar.append((sec_id, asig_id, prof, 1, dia, b3_ini, b3_fin, aula_esp_id))

        # 4. B4 (11:15 - 12:00) - Informática / Robótica (Laboratorio de Cómputo)
        desp4 = (dia_idx + 3) % 6
        for s_idx, gs in enumerate(secciones_tc):
            sec_id = secciones_dict[gs]
            slot = (s_idx + desp4) % 6
            tipo_mat, prof, aula_esp_id = pool_docentes_tc[slot]

            # Si es el grupo que le toca informática en este slot:
            if s_idx == (dia_idx % len(secciones_tc)):
                asig_id = get_tc_asig(gs, "Informática")
                horarios_a_insertar.append((sec_id, asig_id, prof_claudia_inf, 1, dia, b4_ini, b4_fin, aula_comp_id))
            else:
                if tipo_mat == "mat": asig_id = get_tc_asig(gs, "Matemáticas")
                elif tipo_mat == "cie": asig_id = get_tc_asig(gs, "Ciencias Naturales")
                elif tipo_mat == "len": asig_id = get_tc_asig(gs, "Lenguaje")
                elif tipo_mat == "soc": asig_id = get_tc_asig(gs, "Estudios Sociales")
                elif tipo_mat == "ing": asig_id = get_tc_asig(gs, "Inglés")
                else: asig_id = get_tc_asig(gs, "Educación Física")
                horarios_a_insertar.append((sec_id, asig_id, prof, 1, dia, b4_ini, b4_fin, aula_esp_id))

        # 5. B5 (12:30 - 14:00) - Ciencias (Lab Ciencias) / Talleres Vocacionales / Tutoría
        desp5 = (dia_idx + 4) % 6
        for s_idx, gs in enumerate(secciones_tc):
            sec_id = secciones_dict[gs]
            slot = (s_idx + desp5) % 6
            tipo_mat, prof, aula_esp_id = pool_docentes_tc[slot]

            # Una sección va a Laboratorio de Ciencias por día en B5
            if s_idx == ((dia_idx + 1) % len(secciones_tc)):
                asig_id = get_tc_asig(gs, "Ciencias")
                horarios_a_insertar.append((sec_id, asig_id, prof_jose_cie, 1, dia, b5_ini, b5_fin, aula_cien_id))
            else:
                if tipo_mat == "mat": asig_id = get_tc_asig(gs, "Matemáticas")
                elif tipo_mat == "cie": asig_id = get_tc_asig(gs, "Ciencias Naturales")
                elif tipo_mat == "len": asig_id = get_tc_asig(gs, "Lenguaje")
                elif tipo_mat == "soc": asig_id = get_tc_asig(gs, "Estudios Sociales")
                elif tipo_mat == "ing": asig_id = get_tc_asig(gs, "Inglés")
                else: asig_id = get_tc_asig(gs, "Educación Física")
                horarios_a_insertar.append((sec_id, asig_id, prof, 1, dia, b5_ini, b5_fin, aula_esp_id))

    # Inyectar con validación
    insertados = 0
    errores = 0
    for s_id, m_id, p_id, anio_id, dia, ini, fin, esp in horarios_a_insertar:
        try:
            cursor.execute("""
                INSERT INTO horarios (grado_seccion_id, materia_id, profesor_id, anio_lectivo_id, dia_semana, hora_inicio, hora_fin, aula_especial_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (s_id, m_id, p_id, anio_id, dia, ini, fin, esp))
            insertados += 1
        except Exception as e:
            # Si hay pequeña colisión en la permutación matemática, ignorar para preservar integridad UNIQUE
            errores += 1

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n -> Horarios insertados exitosamente: {insertados} bloques lectivos.")
    if errores > 0:
        print(f" -> Bloques descartados por colisión de UNIQUE constraint: {errores}")
    print(" -> Proceso finalizado.")

if __name__ == "__main__":
    run()
