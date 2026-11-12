from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .services import api_client, reports
from .models import ConfiguracionInstitucion, PerfilUsuario

def get_role(user):
    if not user.is_authenticated:
        return None
    if hasattr(user, 'perfil'):
        return user.perfil.rol
    if user.is_superuser:
        return 'Director'
    return 'Secretaria'

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        # 1. Intentar autenticación directa por username en Django
        user = authenticate(request, username=u, password=p)

        # 2. Si no autentica por username, buscar por correo institucional en Django
        if user is None:
            from django.contrib.auth.models import User
            dj_user = User.objects.filter(email__iexact=u).first() or User.objects.filter(username__iexact=u).first()
            if dj_user:
                user = authenticate(request, username=dj_user.username, password=p)

        # 3. Si aún no está en Django, validar contra la API institucional (FastAPI / MySQL)
        if user is None:
            ok, auth_data = api_client.api_login(u, p)
            if ok and isinstance(auth_data, dict):
                usr_data = auth_data.get("usuario", {})
                correo = usr_data.get("correo", u).lower()
                nombre = usr_data.get("nombre", u)
                rol = usr_data.get("rol", "Secretaria")

                from django.contrib.auth.models import User
                dj_user, created = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
                dj_user.set_password(p)
                dj_user.save()

                PerfilUsuario.objects.update_or_create(
                    user=dj_user,
                    defaults={"rol": rol}
                )
                user = authenticate(request, username=correo, password=p)

        if user is not None:
            if not user.is_active:
                messages.error(request, "Acceso denegado: Esta cuenta se encuentra suspendida.")
            else:
                login(request, user)
                rol = get_role(user)
                messages.success(request, f"Sesión iniciada correctamente. Perfil: {rol}.")
                return redirect('dashboard')
        else:
            messages.error(request, "Credenciales incorrectas. Verifique su usuario y contraseña.")


    institucion = ConfiguracionInstitucion.get_activa()
    return render(request, 'portal/login.html', {'institucion': institucion})

def logout_view(request):
    logout(request)
    return redirect('login')

# ==================== DASHBOARD ====================
@login_required
def dashboard(request):
    estudiantes = api_client.get_estudiantes()
    profesores = api_client.get_profesores()
    periodos = api_client.get_periodos()
    
    # Conteos dinámicos reales desde la base de datos
    total_estudiantes = len(estudiantes) if estudiantes else 0
    total_docentes = len(profesores) if profesores else 0
    
    # Secciones activas reales basadas en estudiantes matriculados
    secciones_set = set([e.get("grado_seccion") for e in estudiantes if e.get("grado_seccion")])
    secciones_activas = len(secciones_set) if secciones_set else 0

    periodos_display = []
    if periodos:
        for p in periodos:
            periodos_display.append({
                "id": p.get("id"),
                "nombre": p.get("nombre"),
                "estado": p.get("estado", "Abierto"),
                "anio_lectivo_id": p.get("anio_lectivo_id", 1),
                "vigencia": "Año Lectivo Activo",
                "avance": 100 if p.get("estado") == "Cerrado" else 84
            })

    context = {
        "total_estudiantes": total_estudiantes,
        "total_docentes": total_docentes,
        "secciones_activas": secciones_activas,
        "alumnos_riesgo": 0,
        "periodos": periodos_display,
        "rol_actual": get_role(request.user),
    }
    return render(request, "portal/dashboard.html", context)

# ==================== ESTUDIANTES / MATRÍCULA ====================
@login_required
def estudiantes_list(request):
    query = request.GET.get("q", "").strip().lower()
    estudiantes = api_client.get_estudiantes()
    rol = get_role(request.user)
    
    if query and estudiantes:
        estudiantes = [
            e for e in estudiantes
            if query in str(e.get("nie", "")).lower() or query in str(e.get("nombre_completo", "")).lower()
        ]

    context = {
        "estudiantes": estudiantes,
        "query": query,
        "total": len(estudiantes) if estudiantes else 0,
        "puede_matricular": (rol == 'Secretaria'),
        "rol_actual": rol,
    }
    return render(request, "portal/estudiantes.html", context)

@login_required
def estudiantes_export_pdf(request):
    query = request.GET.get("q", "").strip().lower()
    estudiantes = api_client.get_estudiantes() or []
    if query:
        estudiantes = [
            e for e in estudiantes
            if query in str(e.get("nie", "")).lower() or query in str(e.get("nombre_completo", "")).lower()
        ]
    institucion = ConfiguracionInstitucion.get_activa()
    pdf_bytes = reports.generar_pdf_estudiantes(estudiantes, institucion, query=query)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Padron_Estudiantes.pdf"'
    return response

@login_required
def estudiantes_export_excel(request):
    query = request.GET.get("q", "").strip().lower()
    estudiantes = api_client.get_estudiantes() or []
    if query:
        estudiantes = [
            e for e in estudiantes
            if query in str(e.get("nie", "")).lower() or query in str(e.get("nombre_completo", "")).lower()
        ]
    institucion = ConfiguracionInstitucion.get_activa()
    excel_bytes = reports.generar_excel_estudiantes(estudiantes, institucion)
    response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Padron_Estudiantes.xlsx"'
    return response

@login_required
def estudiante_create(request):
    rol = get_role(request.user)
    if rol not in ['Secretaria', 'Director']:
        messages.error(request, "Acceso Denegado: La matrícula es responsabilidad exclusiva de Secretaría.")
        return redirect('estudiantes_list')

    if request.method == "POST":
        nie = request.POST.get("nie", "").strip()
        nombre_completo = request.POST.get("nombre_completo", "").strip()
        if not nombre_completo:
            nombres = request.POST.get("nombres", "").strip()
            apellidos = request.POST.get("apellidos", "").strip()
            if nombres or apellidos:
                nombre_completo = f"{nombres} {apellidos}".strip()
            else:
                nombre_completo = request.POST.get("nombre", "").strip()
        grado_seccion = request.POST.get("grado_seccion", "").strip()
        encargado = request.POST.get("encargado", "").strip()
        telefono = request.POST.get("telefono", "").strip()

        if not nie or not nombre_completo:
            messages.error(request, "NIE y Nombre son obligatorios.")
            return redirect("estudiantes_list")

        data = {
            "nie": nie,
            "nombre_completo": nombre_completo,
            "grado_seccion": grado_seccion,
            "encargado": encargado,
            "telefono": telefono,
            "fecha_nacimiento": request.POST.get("fecha_nacimiento", "").strip() or "No especificada",
            "direccion": request.POST.get("direccion", "").strip() or "No especificada",
            "alergias": request.POST.get("alergias", "").strip() or "Ninguna conocida",
            "condiciones_medicas": request.POST.get("condiciones_medicas", "").strip() or "Ninguna reportada",
        }
        success, res = api_client.create_estudiante(data)
        if success:
            messages.success(request, f"¡Estudiante {nombre_completo} (NIE: {nie}) matriculado correctamente!")
        else:
            messages.error(request, f"Error: No se pudo matricular. Verifique que el NIE {nie} no esté repetido.")

    return redirect("estudiantes_list")

@login_required
def estudiante_update(request, id):
    rol = get_role(request.user)
    if rol not in ['Secretaria', 'Director']:
        messages.error(request, "Acceso Denegado: Solo Secretaría puede modificar expedientes.")
        return redirect('estudiantes_list')

    if request.method == "POST":
        nombres = request.POST.get("nombres", "").strip()
        apellidos = request.POST.get("apellidos", "").strip()
        if nombres or apellidos:
            nom_comp = f"{nombres} {apellidos}".strip()
        else:
            nom_comp = (request.POST.get("nombre_completo") or request.POST.get("nombre") or "").strip()

        data = {
            "nie": request.POST.get("nie", "").strip(),
            "nombre_completo": nom_comp,
            "grado_seccion": request.POST.get("grado_seccion", "").strip(),
            "encargado": request.POST.get("encargado", "").strip(),
            "telefono": request.POST.get("telefono", "").strip(),
            "fecha_nacimiento": request.POST.get("fecha_nacimiento", "").strip() or "No especificada",
            "direccion": request.POST.get("direccion", "").strip() or "No especificada",
            "alergias": request.POST.get("alergias", "").strip() or "Ninguna conocida",
            "condiciones_medicas": request.POST.get("condiciones_medicas", "").strip() or "Ninguna reportada",
        }
        success, _ = api_client.update_estudiante(id, data)
        if success:
            messages.success(request, "Expediente actualizado exitosamente.")
        else:
            messages.error(request, "Error al actualizar estudiante.")

    return redirect("estudiantes_list")

@login_required
def estudiante_delete(request, id):
    rol = get_role(request.user)
    if rol not in ['Secretaria', 'Director']:
        messages.error(request, "Acceso Denegado: Solo Secretaría puede dar de baja estudiantes.")
        return redirect('estudiantes_list')

    if request.method == "POST":
        if api_client.delete_estudiante(id):
            messages.success(request, "Estudiante eliminado del padrón.")
        else:
            messages.error(request, "No se pudo eliminar el estudiante.")
    return redirect("estudiantes_list")

# ==================== DOCENTES / PROFESORES ====================
@login_required
def docentes_list(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: La administración de la planta docente es competencia exclusiva de Dirección General.")
        return redirect('dashboard')

    profesores = api_client.get_profesores()
    context = {
        "profesores": profesores,
        "total": len(profesores),
        "rol_actual": rol,
    }
    return render(request, "portal/docentes.html", context)

@login_required
def docente_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede registrar docentes.")
        return redirect('dashboard')

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        correo = request.POST.get("correo", "").strip().lower()
        telefono = request.POST.get("telefono", "").strip()
        especialidad = request.POST.get("especialidad", "").strip()
        password = request.POST.get("password", "").strip() or "docente123"

        if not nombre or not correo:
            messages.error(request, "Nombre y Correo electrónico son obligatorios.")
            return redirect("docentes_list")

        data = {
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "especialidad": especialidad,
            "password": password
        }
        success, res = api_client.create_profesor(data)
        if success:
            # Sincronizar en Django User para acceso al portal web
            from django.contrib.auth.models import User
            dj_user, created = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
            dj_user.set_password(password)
            dj_user.save()
            PerfilUsuario.objects.update_or_create(user=dj_user, defaults={"rol": "Profesor"})
            messages.success(request, f"Docente {nombre} registrado exitosamente con clave asignada.")
        else:
            messages.error(request, "Error: El correo electrónico ya pertenece a otro usuario.")

    return redirect("docentes_list")

@login_required
def docente_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede eliminar docentes.")
        return redirect('dashboard')

    if request.method == "POST":
        # Identificar el nombre del docente antes de eliminarlo
        profesores = api_client.get_profesores()
        prof_obj = next((p for p in profesores if p.get('id') == id), None)
        nombre_docente = prof_obj.get('nombre') if prof_obj else None

        if api_client.delete_profesor(id):
            # Si tenía asignaturas asignadas, liberarlas a 'Sin asignar' para que el Director las reasigne
            if nombre_docente:
                asignaturas = api_client.get_asignaturas()
                liberadas = 0
                for a in asignaturas:
                    if a.get('profesor_nombre') == nombre_docente:
                        api_client.update_asignatura(a.get('id'), {
                            "codigo": a.get('codigo'),
                            "nombre": a.get('nombre'),
                            "grado_seccion": a.get('grado_seccion'),
                            "profesor_nombre": "Sin asignar",
                            "descripcion": a.get('descripcion')
                        })
                        liberadas += 1
                if liberadas > 0:
                    messages.warning(request, f"Docente eliminado. {liberadas} asignatura(s) quedaron 'Sin asignar' para que pueda asignarlas a otro docente en Carga Académica.")
                else:
                    messages.success(request, "Docente eliminado correctamente.")
            else:
                messages.success(request, "Docente eliminado correctamente.")
        else:
            messages.error(request, "No se pudo eliminar el docente.")
    return redirect("docentes_list")

# ==================== ASIGNATURAS / CARGA ACADÉMICA ====================
@login_required
def carga_academica(request):
    asignaturas = api_client.get_asignaturas() or []
    profesores = api_client.get_profesores() or []
    secciones = api_client.get_secciones() or []
    rol = get_role(request.user)

    # Identificar Ciclo Educativo
    def obtener_ciclo(gs):
        gs_clean = (gs or "").lower()
        if any(x in gs_clean for x in ["7", "8", "9"]):
            return "Tercer Ciclo (7º a 9º Grado)"
        elif any(x in gs_clean for x in ["4", "5", "6"]):
            return "Segundo Ciclo (4º a 6º Grado)"
        elif any(x in gs_clean for x in ["1", "2", "3"]):
            return "Primer Ciclo (1º a 3º Grado)"
        return "Ciclo General"

    # Consolidar asignaturas por Materia y Ciclo para visualización ejecutiva
    cargas_dict = {}
    for a in asignaturas:
        materia = a.get("nombre", "").strip()
        materia = " ".join(materia.split())
        prof_nom = a.get("profesor_nombre", "Sin asignar").strip()
        ciclo = obtener_ciclo(a.get("grado_seccion", ""))
        sec = a.get("grado_seccion", "General")

        key = (ciclo, materia)
        if key not in cargas_dict:
            cargas_dict[key] = {
                "ciclo": ciclo,
                "materia": materia,
                "profesor_nombre": prof_nom,
                "secciones": [],
                "ids": [],
                "codigos": [],
                "profesores_set": set(),
            }
        if sec not in cargas_dict[key]["secciones"]:
            cargas_dict[key]["secciones"].append(sec)
        cargas_dict[key]["ids"].append(str(a.get("id")))
        cargas_dict[key]["codigos"].append(a.get("codigo"))
        if prof_nom and prof_nom != "Sin asignar":
            cargas_dict[key]["profesores_set"].add(prof_nom)

    for c in cargas_dict.values():
        if c["profesores_set"]:
            c["profesor_nombre"] = ", ".join(sorted(list(c["profesores_set"])))
        else:
            c["profesor_nombre"] = "Sin asignar"

    ciclos_order = {
        "Tercer Ciclo (7º a 9º Grado)": 1,
        "Segundo Ciclo (4º a 6º Grado)": 2,
        "Primer Ciclo (1º a 3º Grado)": 3,
        "Ciclo General": 4
    }

    cargas_consolidadas = sorted(
        cargas_dict.values(),
        key=lambda x: (ciclos_order.get(x["ciclo"], 99), x["materia"])
    )

    for c in cargas_consolidadas:
        c["total_secciones"] = len(c["secciones"])
        abrevs = []
        secciones_items = []
        for s in c["secciones"]:
            parts = s.split(" - ")
            if len(parts) == 2:
                grado_num = parts[0].replace(" Grado", "")
                sec_letra = parts[1].replace("Sección ", "")
                corta = f"{grado_num} {sec_letra}"
            else:
                corta = s
            abrevs.append(corta)
            secciones_items.append({"corta": corta, "completa": s})
        c["secciones_resumen"] = ", ".join(abrevs)
        c["secciones_items"] = secciones_items
        c["ids_str"] = ",".join(c["ids"])
        c["secciones_csv"] = ",".join(c["secciones"])

    # Agrupar por ciclo para la UI
    cargas_por_ciclo = {}
    for c in cargas_consolidadas:
        ciclo = c["ciclo"]
        if ciclo not in cargas_por_ciclo:
            cargas_por_ciclo[ciclo] = []
        cargas_por_ciclo[ciclo].append(c)

    ciclos_estructura = [
        {
            "ciclo": "Tercer Ciclo (7º a 9º Grado)",
            "ciclo_id": "c3",
            "grados": [
                {"grado": "7° Grado", "num": "7", "sec_a": "7° Grado - Sección A", "sec_b": "7° Grado - Sección B"},
                {"grado": "8° Grado", "num": "8", "sec_a": "8° Grado - Sección A", "sec_b": "8° Grado - Sección B"},
                {"grado": "9° Grado", "num": "9", "sec_a": "9° Grado - Sección A", "sec_b": "9° Grado - Sección B"},
            ]
        },
        {
            "ciclo": "Segundo Ciclo (4º a 6º Grado)",
            "ciclo_id": "c2",
            "grados": [
                {"grado": "4° Grado", "num": "4", "sec_a": "4° Grado - Sección A", "sec_b": "4° Grado - Sección B"},
                {"grado": "5° Grado", "num": "5", "sec_a": "5° Grado - Sección A", "sec_b": "5° Grado - Sección B"},
                {"grado": "6° Grado", "num": "6", "sec_a": "6° Grado - Sección A", "sec_b": "6° Grado - Sección B"},
            ]
        },
        {
            "ciclo": "Primer Ciclo (1º a 3º Grado)",
            "ciclo_id": "c1",
            "grados": [
                {"grado": "1° Grado", "num": "1", "sec_a": "1° Grado - Sección A", "sec_b": "1° Grado - Sección B"},
                {"grado": "2° Grado", "num": "2", "sec_a": "2° Grado - Sección A", "sec_b": "2° Grado - Sección B"},
                {"grado": "3° Grado", "num": "3", "sec_a": "3° Grado - Sección A", "sec_b": "3° Grado - Sección B"},
            ]
        }
    ]

    context = {
        "cargas_consolidadas": cargas_consolidadas,
        "cargas_por_ciclo": cargas_por_ciclo,
        "ciclos_estructura": ciclos_estructura,
        "asignaturas": asignaturas,
        "profesores": profesores,
        "secciones": secciones,
        "total_cargas": len(cargas_consolidadas),
        "total": len(asignaturas),
        "rol_actual": rol,
    }
    return render(request, "portal/carga_academica.html", context)

@login_required
def carga_academica_reasignar_materia(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede reasignar cargas académicas.")
        return redirect("carga_academica")

    if request.method == "POST":
        materia = request.POST.get("materia", "").strip()
        ciclo = request.POST.get("ciclo", "").strip()
        nuevo_profesor_nombre = request.POST.get("nuevo_profesor_nombre", "").strip()
        asignatura_ids = request.POST.get("asignatura_ids", "").strip()

        if not nuevo_profesor_nombre or not asignatura_ids:
            messages.error(request, "Debe seleccionar un docente para reasignar la materia.")
            return redirect("carga_academica")

        ids_list = [int(x.strip()) for x in asignatura_ids.split(",") if x.strip().isdigit()]

        # 1. Actualizar directamente en MySQL con commit inmediato en asignaturas
        try:
            import MySQLdb
            conn = MySQLdb.connect(
                host='127.0.0.1', user='root', passwd='', db='control_escolar_db', charset='utf8mb4'
            )
            cur = conn.cursor()

            # Buscar profesor_id por nombre
            cur.execute("""
                SELECT p.id 
                FROM profesores p 
                JOIN usuarios u ON p.usuario_id = u.id 
                WHERE u.nombre LIKE %s OR u.nombre = %s
                LIMIT 1;
            """, (f"%{nuevo_profesor_nombre}%", nuevo_profesor_nombre))
            row = cur.fetchone()
            nuevo_prof_id = row[0] if row else None

            # Actualizar y confirmar asignaturas
            format_strings = ','.join(['%s'] * len(ids_list))
            cur.execute(f"""
                UPDATE asignaturas 
                SET profesor_nombre = %s 
                WHERE id IN ({format_strings});
            """, [nuevo_profesor_nombre] + ids_list)
            conn.commit()

            # Actualizar cargas_academicas
            if nuevo_prof_id:
                try:
                    cur.execute("""
                        SELECT id FROM materias WHERE nombre_materia = %s LIMIT 1;
                    """, (materia,))
                    mat_row = cur.fetchone()
                    if mat_row:
                        mat_id = mat_row[0]
                        cur.execute(f"""
                            SELECT DISTINCT gs.id
                            FROM asignaturas a
                            JOIN grados_secciones gs ON gs.grado = TRIM(SUBSTRING_INDEX(a.grado_seccion, '-', 1))
                                                     AND gs.seccion = TRIM(SUBSTRING_INDEX(a.grado_seccion, '-', -1))
                            WHERE a.id IN ({format_strings});
                        """, ids_list)
                        sec_ids = [r[0] for r in cur.fetchall()]
                        if sec_ids:
                            format_sec = ','.join(['%s'] * len(sec_ids))
                            cur.execute(f"""
                                UPDATE cargas_academicas 
                                SET profesor_id = %s 
                                WHERE materia_id = %s AND grado_seccion_id IN ({format_sec});
                            """, [nuevo_prof_id, mat_id] + sec_ids)
                            conn.commit()
                except Exception:
                    pass

                # Actualizar horarios de forma segura slot por slot
                try:
                    cur.execute(f"""
                        SELECT id, dia_semana, hora_inicio, hora_fin, anio_lectivo_id
                        FROM horarios
                        WHERE materia_id IN ({format_strings});
                    """, ids_list)
                    horarios_slots = cur.fetchall()
                    for h_id, dia, h_ini, h_fin, anio_id in horarios_slots:
                        cur.execute("""
                            SELECT id FROM horarios 
                            WHERE profesor_id = %s AND dia_semana = %s AND hora_inicio = %s AND hora_fin = %s AND anio_lectivo_id = %s
                            LIMIT 1;
                        """, (nuevo_prof_id, dia, h_ini, h_fin, anio_id))
                        ocupado = cur.fetchone()
                        if not ocupado:
                            cur.execute("UPDATE horarios SET profesor_id = %s WHERE id = %s;", (nuevo_prof_id, h_id))
                    conn.commit()
                except Exception:
                    pass

            conn.close()
        except Exception:
            pass

        # 2. Sincronizar vía API
        for asig_id in ids_list:
            api_client.update_asignatura(asig_id, {"profesor_nombre": nuevo_profesor_nombre})

        messages.success(request, f"Materia '{materia}' ({ciclo}) reasignada con éxito a {nuevo_profesor_nombre}.")

    return redirect("carga_academica")

def generar_codigo_seccion(codigo_base, grado_seccion, existentes=None):
    """
    Genera un código limpio y único para una materia en una sección específica.
    Ej: base='PI-II', grado_seccion='9° Grado - Sección A' -> 'PI-II-9A'
    """
    import re
    g_match = re.search(r'(\d+)', grado_seccion or "")
    s_match = re.search(r'Secci[oó]n\s+([A-Za-z0-9])', grado_seccion or "", re.IGNORECASE)

    g_num = g_match.group(1) if g_match else ""
    s_letra = s_match.group(1).upper() if s_match else ""
    sufijo = f"{g_num}{s_letra}".strip()

    base = (codigo_base or "ASIG").strip().upper()
    if sufijo and base.endswith(f"-{sufijo}"):
        candidate = base
    elif sufijo:
        candidate = f"{base}-{sufijo}"
    else:
        candidate = base

    if not existentes:
        return candidate

    orig = candidate
    c = 1
    while candidate in existentes:
        candidate = f"{orig}-{c}"
        c += 1
    return candidate

@login_required
def asignatura_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede crear asignaturas.")
        return redirect("carga_academica")

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        nombre = " ".join(nombre.split())
        profesor_nombre = request.POST.get("profesor_nombre", "").strip() or "Sin asignar"
        descripcion = request.POST.get("descripcion", "").strip()

        # Permitir selección múltiple de grados/secciones
        secciones = request.POST.getlist("secciones")
        if not secciones:
            grado_seccion = request.POST.get("grado_seccion", "").strip()
            if grado_seccion:
                secciones = [grado_seccion]

        if not codigo or not nombre:
            messages.error(request, "El código base y el nombre de la asignatura son obligatorios.")
            return redirect("carga_academica")

        if not secciones:
            messages.error(request, "Debe seleccionar al menos un grado o sección para la asignatura.")
            return redirect("carga_academica")

        try:
            import MySQLdb
            conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='', db='control_escolar_db', charset='utf8mb4')
            cur = conn.cursor()

            # 1. Asegurar registro en materias
            cur.execute("SELECT id FROM materias WHERE nombre_materia = %s LIMIT 1;", (nombre,))
            row_mat = cur.fetchone()
            if row_mat:
                materia_id = row_mat[0]
            else:
                cur.execute("INSERT INTO materias (nombre_materia, descripcion) VALUES (%s, %s);", (nombre, descripcion or f"Materia {nombre}"))
                materia_id = cur.lastrowid
                conn.commit()

            # 2. Profesor ID
            profesor_id = None
            if profesor_nombre and profesor_nombre != "Sin asignar":
                cur.execute("""
                    SELECT p.id FROM profesores p
                    JOIN usuarios u ON p.usuario_id = u.id
                    WHERE u.nombre LIKE %s OR u.nombre = %s
                    LIMIT 1;
                """, (f"%{profesor_nombre}%", profesor_nombre))
                row_prof = cur.fetchone()
                if row_prof:
                    profesor_id = row_prof[0]

            # 3. Códigos existentes
            cur.execute("SELECT codigo FROM asignaturas;")
            existentes = {r[0] for r in cur.fetchall()}

            for sec in secciones:
                cod_final = generar_codigo_seccion(codigo, sec, existentes)
                existentes.add(cod_final)

                cur.execute("SELECT id FROM asignaturas WHERE nombre = %s AND grado_seccion = %s LIMIT 1;", (nombre, sec))
                asig_existente = cur.fetchone()
                if asig_existente:
                    cur.execute("UPDATE asignaturas SET profesor_nombre = %s, descripcion = %s WHERE id = %s;", (profesor_nombre, descripcion, asig_existente[0]))
                else:
                    cur.execute("""
                        INSERT INTO asignaturas (codigo, nombre, grado_seccion, profesor_nombre, descripcion)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (cod_final, nombre, sec, profesor_nombre, descripcion))

                # Vincular en cargas_academicas
                if profesor_id and materia_id:
                    parts = sec.split(" - ")
                    if len(parts) == 2:
                        cur.execute("SELECT id FROM grados_secciones WHERE grado = %s AND seccion = %s LIMIT 1;", (parts[0].strip(), parts[1].strip()))
                        gs = cur.fetchone()
                        if gs:
                            gs_id = gs[0]
                            cur.execute("SELECT id FROM cargas_academicas WHERE materia_id = %s AND grado_seccion_id = %s LIMIT 1;", (materia_id, gs_id))
                            ca = cur.fetchone()
                            if ca:
                                cur.execute("UPDATE cargas_academicas SET profesor_id = %s WHERE id = %s;", (profesor_id, ca[0]))
                            else:
                                cur.execute("INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id) VALUES (%s, %s, %s);", (profesor_id, materia_id, gs_id))

            conn.commit()
            conn.close()
            messages.success(request, f"Asignatura '{nombre}' asignada exitosamente a {len(secciones)} sección(es).")
        except Exception as e:
            # Fallback API
            for sec in secciones:
                cod_final = generar_codigo_seccion(codigo, sec)
                api_client.create_asignatura({
                    "codigo": cod_final,
                    "nombre": nombre,
                    "grado_seccion": sec,
                    "profesor_nombre": profesor_nombre,
                    "descripcion": descripcion
                })
            messages.success(request, f"Asignatura '{nombre}' registrada para {len(secciones)} sección(es).")

    return redirect("carga_academica")

@login_required
def asignatura_gestionar_secciones(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede gestionar las secciones de una asignatura.")
        return redirect("carga_academica")

    if request.method == "POST":
        materia = request.POST.get("materia", "").strip()
        materia = " ".join(materia.split())
        profesor_nombre = request.POST.get("profesor_nombre", "").strip() or "Sin asignar"
        secciones_deseadas = request.POST.getlist("secciones")

        if not materia:
            messages.error(request, "Nombre de materia inválido.")
            return redirect("carga_academica")

        if not secciones_deseadas:
            messages.error(request, "Debe seleccionar al menos una sección para la materia.")
            return redirect("carga_academica")

        try:
            import MySQLdb
            conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='', db='control_escolar_db', charset='utf8mb4')
            cur = conn.cursor()

            # 1. Asignaturas actuales
            cur.execute("SELECT id, codigo, grado_seccion, profesor_nombre FROM asignaturas WHERE nombre = %s;", (materia,))
            actuales = cur.fetchall()
            secciones_actuales = {row[2]: (row[0], row[1]) for row in actuales}

            codigo_base = "ASIG"
            if actuales:
                first_cod = actuales[0][1]
                parts = first_cod.rsplit("-", 1)
                if len(parts) == 2 and any(char.isdigit() for char in parts[1]):
                    codigo_base = parts[0]
                else:
                    codigo_base = first_cod

            # 2. Materia ID
            cur.execute("SELECT id FROM materias WHERE nombre_materia = %s LIMIT 1;", (materia,))
            mat_row = cur.fetchone()
            if not mat_row:
                cur.execute("INSERT INTO materias (nombre_materia) VALUES (%s);", (materia,))
                materia_id = cur.lastrowid
                conn.commit()
            else:
                materia_id = mat_row[0]

            # 3. Profesor ID
            profesor_id = None
            if profesor_nombre and profesor_nombre != "Sin asignar":
                cur.execute("""
                    SELECT p.id FROM profesores p
                    JOIN usuarios u ON p.usuario_id = u.id
                    WHERE u.nombre LIKE %s OR u.nombre = %s LIMIT 1;
                """, (f"%{profesor_nombre}%", profesor_nombre))
                p_row = cur.fetchone()
                if p_row:
                    profesor_id = p_row[0]

            set_deseadas = set(secciones_deseadas)
            set_actuales = set(secciones_actuales.keys())

            agregar = set_deseadas - set_actuales
            eliminar = set_actuales - set_deseadas

            cur.execute("SELECT codigo FROM asignaturas;")
            existentes_codigos = {r[0] for r in cur.fetchall()}

            for sec in agregar:
                cod_final = generar_codigo_seccion(codigo_base, sec, existentes_codigos)
                existentes_codigos.add(cod_final)
                cur.execute("""
                    INSERT INTO asignaturas (codigo, nombre, grado_seccion, profesor_nombre, descripcion)
                    VALUES (%s, %s, %s, %s, %s);
                """, (cod_final, materia, sec, profesor_nombre, f"Materia {materia}"))

                if profesor_id and materia_id:
                    parts = sec.split(" - ")
                    if len(parts) == 2:
                        cur.execute("SELECT id FROM grados_secciones WHERE grado = %s AND seccion = %s LIMIT 1;", (parts[0].strip(), parts[1].strip()))
                        gs = cur.fetchone()
                        if gs:
                            gs_id = gs[0]
                            cur.execute("SELECT id FROM cargas_academicas WHERE materia_id = %s AND grado_seccion_id = %s LIMIT 1;", (materia_id, gs_id))
                            ca = cur.fetchone()
                            if ca:
                                cur.execute("UPDATE cargas_academicas SET profesor_id = %s WHERE id = %s;", (profesor_id, ca[0]))
                            else:
                                cur.execute("INSERT INTO cargas_academicas (profesor_id, materia_id, grado_seccion_id) VALUES (%s, %s, %s);", (profesor_id, materia_id, gs_id))

            for sec in eliminar:
                asig_id, _ = secciones_actuales[sec]
                cur.execute("DELETE FROM asignaturas WHERE id = %s;", (asig_id,))
                if materia_id:
                    parts = sec.split(" - ")
                    if len(parts) == 2:
                        cur.execute("SELECT id FROM grados_secciones WHERE grado = %s AND seccion = %s LIMIT 1;", (parts[0].strip(), parts[1].strip()))
                        gs = cur.fetchone()
                        if gs:
                            cur.execute("DELETE FROM cargas_academicas WHERE materia_id = %s AND grado_seccion_id = %s;", (materia_id, gs[0]))

            conn.commit()
            conn.close()
            messages.success(request, f"Secciones actualizadas para '{materia}': ahora atiende a {len(secciones_deseadas)} sección(es).")
        except Exception as e:
            messages.error(request, f"Error al actualizar secciones: {str(e)}")

    return redirect("carga_academica")

@login_required
def asignatura_update(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede reasignar o editar asignaturas.")
        return redirect("carga_academica")

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip()
        nombre = request.POST.get("nombre", "").strip()
        grado_seccion = request.POST.get("grado_seccion", "").strip() or "General"
        profesor_nombre = request.POST.get("profesor_nombre", "").strip() or "Sin asignar"
        descripcion = request.POST.get("descripcion", "").strip()

        if not codigo or not nombre:
            messages.error(request, "El código y el nombre de la asignatura son obligatorios.")
            return redirect("carga_academica")

        data = {
            "codigo": codigo,
            "nombre": nombre,
            "grado_seccion": grado_seccion,
            "profesor_nombre": profesor_nombre,
            "descripcion": descripcion
        }

        # Actualizar en MySQL directamente
        try:
            import MySQLdb
            conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='', db='control_escolar_db', charset='utf8mb4')
            cur = conn.cursor()
            cur.execute("""
                UPDATE asignaturas 
                SET codigo = %s, nombre = %s, grado_seccion = %s, profesor_nombre = %s, descripcion = %s
                WHERE id = %s;
            """, (codigo, nombre, grado_seccion, profesor_nombre, descripcion, id))
            conn.commit()

            cur.execute("""
                SELECT p.id FROM profesores p 
                JOIN usuarios u ON p.usuario_id = u.id 
                WHERE u.nombre LIKE %s OR u.nombre = %s LIMIT 1;
            """, (f"%{profesor_nombre}%", profesor_nombre))
            p_row = cur.fetchone()
            if p_row:
                try:
                    cur.execute("UPDATE horarios SET profesor_id = %s WHERE materia_id = %s;", (p_row[0], id))
                    conn.commit()
                except Exception:
                    pass
            conn.close()
        except Exception:
            pass

        # Actualizar vía API
        api_client.update_asignatura(id, data)
        messages.success(request, f"Asignatura '{nombre}' ({codigo}) actualizada. Docente asignado: {profesor_nombre}.")

    return redirect("carga_academica")

@login_required
def asignatura_delete(request, id):
    if request.method == "POST":
        if api_client.delete_asignatura(id):
            messages.success(request, "Asignatura eliminada correctamente.")
        else:
            messages.error(request, "No se pudo eliminar la asignatura.")
    return redirect("carga_academica")

# ==================== CICLOS Y PERIODOS ESCOLARES ====================
@login_required
def periodos_list(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: El control de cierres de período es exclusivo de Dirección General.")
        return redirect('dashboard')

    periodos = api_client.get_periodos()
    anios = api_client.get_anios()
    context = {
        "periodos": periodos,
        "anios": anios,
        "puede_cerrar": True,
        "rol_actual": rol,
    }
    return render(request, "portal/periodos.html", context)

@login_required
def anio_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Solo la Dirección General puede crear nuevos años lectivos.")
        return redirect("periodos_list")

    if request.method == "POST":
        anio = request.POST.get("anio", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        estado = request.POST.get("estado", "Activo")

        if not anio:
            messages.error(request, "El año lectivo es obligatorio (ej: 2027).")
            return redirect("periodos_list")

        data = {"anio": anio, "descripcion": descripcion, "estado": estado}
        success, _ = api_client.create_anio(data)
        if success:
            messages.success(request, f"¡Año lectivo {anio} creado con éxito!")
        else:
            messages.error(request, "El año lectivo ya se encuentra registrado.")

    return redirect("periodos_list")

@login_required
def anio_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso denegado: Solo el Director General puede eliminar años lectivos.")
        return redirect("periodos_list")

    if request.method == "POST":
        success, msg = api_client.delete_anio(id)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, f"No se pudo eliminar el año lectivo: {msg}")
    return redirect("periodos_list")

@login_required
def anio_toggle_estado(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso denegado: Solo la Dirección General puede cambiar el estado de los años lectivos.")
        return redirect("periodos_list")

    if request.method == "POST":
        anios = api_client.get_anios()
        target = next((a for a in anios if a.get("id") == id), None)
        if target:
            actual = target.get("estado", "Activo")
            nuevo = "Cerrado" if actual in ["Activo", "Planificado"] else "Activo"
            if api_client.toggle_anio_estado(id, nuevo):
                estado_texto = "Finalizado / Concluido" if nuevo == "Cerrado" else "Activo / En Curso"
                messages.success(request, f"Año lectivo {target.get('anio')} marcado como '{estado_texto}'.")
            else:
                messages.error(request, "Error al actualizar el estado del año lectivo.")
    return redirect("periodos_list")


@login_required
def periodo_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Solo la Dirección General puede configurar nuevos períodos.")
        return redirect("periodos_list")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        anio_id = request.POST.get("anio_lectivo_id")
        estado = request.POST.get("estado", "Abierto")

        if not nombre or not anio_id:
            messages.error(request, "Nombre del período y Ciclo son requeridos.")
            return redirect("periodos_list")

        data = {
            "nombre": nombre,
            "anio_lectivo_id": int(anio_id),
            "estado": estado
        }
        success, _ = api_client.create_periodo(data)
        if success:
            messages.success(request, f"¡Período '{nombre}' agregado exitosamente!")
        else:
            messages.error(request, "Error al crear el período escolar.")

    return redirect("periodos_list")

@login_required
def periodo_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso denegado.")
        return redirect("periodos_list")

    if request.method == "POST":
        if api_client.delete_periodo(id):
            messages.success(request, "Período eliminado correctamente.")
        else:
            messages.error(request, "No se pudo eliminar el período.")
    return redirect("periodos_list")

@login_required
def periodo_toggle(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: El control de cierres de período es potestad exclusiva del Director.")
        return redirect('periodos_list')

    if request.method == "POST":
        periodos = api_client.get_periodos()
        target = next((p for p in periodos if p.get("id") == id), None)
        if target:
            nuevo_estado = "Cerrado" if target.get("estado") == "Abierto" else "Abierto"
            ok = api_client.toggle_periodo(
                id,
                target.get("nombre", f"Período {id}"),
                target.get("anio_lectivo_id", 1),
                nuevo_estado
            )
            if ok:
                if nuevo_estado == "Cerrado":
                    messages.success(request, f"¡{target.get('nombre')} CERRADO! Calificaciones asentadas y boletas de notas habilitadas para entrega.")
                else:
                    messages.success(request, f"¡{target.get('nombre')} REABIERTO! El registro de notas por docentes ha sido reactivado.")
            else:
                messages.error(request, "Error al actualizar estado en la API.")
    return redirect('periodos_list')

# ==================== BOLETAS DE CALIFICACIONES ====================
def get_boletas_data(seccion_filtro=None, periodo_id=None, estudiante_id=None):
    estudiantes_raw = api_client.get_estudiantes() or []
    asignaturas_raw = api_client.get_asignaturas() or []
    periodos_raw = api_client.get_periodos() or []
    calificaciones_raw = api_client.get_calificaciones() or []

    periodo_obj = None
    if periodo_id:
        periodo_obj = next((p for p in periodos_raw if str(p.get("id")) == str(periodo_id)), None)
    if not periodo_obj and periodos_raw:
        # Priorizar el período cerrado más reciente donde las boletas ya están emitidas
        periodos_cerrados = [p for p in periodos_raw if p.get("estado") == "Cerrado"]
        if periodos_cerrados:
            periodo_obj = periodos_cerrados[-1]
        else:
            periodo_obj = periodos_raw[0]

    pid = periodo_obj.get("id") if periodo_obj else None
    periodo_nombre = periodo_obj.get("nombre", "Período 1") if periodo_obj else "Período 1"

    target_estudiantes = []
    for e in estudiantes_raw:
        if seccion_filtro and e.get("grado_seccion") != seccion_filtro:
            continue
        if estudiante_id and str(e.get("id")) != str(estudiante_id):
            continue
        target_estudiantes.append(e)

    califs_by_est_asig = {}
    for c in calificaciones_raw:
        if pid and c.get("periodo_id") != pid:
            continue
        e_id = c.get("estudiante_id")
        a_id = c.get("asignatura_id")
        key = (e_id, a_id)
        if key not in califs_by_est_asig:
            califs_by_est_asig[key] = []
        califs_by_est_asig[key].append(c)

    boletas = []
    for e in target_estudiantes:
        e_id = e.get("id")
        e_seccion = e.get("grado_seccion")

        sec_asigs = [a for a in asignaturas_raw if a.get("grado_seccion") == e_seccion]
        if not sec_asigs:
            sec_asigs = asignaturas_raw

        materias_list = []
        sum_promedios = 0.0

        for a in sec_asigs:
            a_id = a.get("id")
            c_list = califs_by_est_asig.get((e_id, a_id), [])

            act1 = None
            act2 = None
            act3 = None
            direct_nota = None

            for c in c_list:
                tipo = (c.get("tipo_evaluacion") or "").lower()
                n = float(c.get("nota", 0.0))
                if "actividad 1" in tipo or "examen" in tipo or "parcial" in tipo:
                    act1 = n
                elif "actividad 2" in tipo or "tarea" in tipo or "práctica" in tipo or "practica" in tipo:
                    act2 = n
                elif "actividad 3" in tipo or "proyecto" in tipo or "cotidiano" in tipo:
                    act3 = n
                else:
                    direct_nota = n

            acts_present = [x for x in [act1, act2, act3] if x is not None]
            if len(acts_present) == 3:
                m_prom = round((act1 * 0.35) + (act2 * 0.35) + (act3 * 0.30), 1)
            elif len(acts_present) > 0:
                m_prom = round(sum(acts_present) / len(acts_present), 1)
            elif direct_nota is not None:
                m_prom = round(direct_nota, 1)
            else:
                m_prom = 0.0

            materias_list.append({
                "id": a_id,
                "nombre": a.get("nombre", f"Materia #{a_id}"),
                "codigo": a.get("codigo", ""),
                "profesor_nombre": a.get("profesor_nombre", "Docente asignado"),
                "act1": act1,
                "act2": act2,
                "act3": act3,
                "promedio": m_prom,
                "aprobado": m_prom >= 6.0,
            })
            sum_promedios += m_prom

        prom_general = round(sum_promedios / len(materias_list), 2) if materias_list else 0.0

        boletas.append({
            "estudiante": e,
            "materias": materias_list,
            "promedio_general": prom_general,
            "aprobado": prom_general >= 6.0,
            "periodo_nombre": periodo_nombre,
        })

    secciones = sorted(list(set([e.get("grado_seccion") for e in estudiantes_raw if e.get("grado_seccion")])))
    return boletas, periodo_nombre, periodo_obj, periodos_raw, secciones

@login_required
def boletas_view(request):
    seccion = request.GET.get("seccion", "").strip()
    periodo_id = request.GET.get("periodo_id", "").strip()
    estudiante_id = request.GET.get("estudiante_id", "").strip()

    boletas, periodo_nombre, periodo_obj, periodos, secciones = get_boletas_data(
        seccion_filtro=seccion,
        periodo_id=periodo_id,
        estudiante_id=estudiante_id
    )

    institucion = ConfiguracionInstitucion.get_activa()
    rol = get_role(request.user)
    periodo_cerrado = (periodo_obj.get("estado") == "Cerrado") if periodo_obj else False

    # Conteo de alumnos por seccion para los filtros rápidos en interfaz
    estudiantes_raw = api_client.get_estudiantes() or []
    conteo_por_seccion = {}
    for e in estudiantes_raw:
        s = e.get("grado_seccion")
        if s:
            conteo_por_seccion[s] = conteo_por_seccion.get(s, 0) + 1

    secciones_con_conteo = [
        {"nombre": s, "total": conteo_por_seccion.get(s, 0)}
        for s in secciones
    ]

    context = {
        "boletas": boletas,
        "periodo_nombre": periodo_nombre,
        "periodo_obj": periodo_obj,
        "periodo_cerrado": periodo_cerrado,
        "periodos": periodos,
        "secciones": secciones,
        "secciones_con_conteo": secciones_con_conteo,
        "total_alumnos_colegio": len(estudiantes_raw),
        "seccion_filtro": seccion,
        "periodo_filtro": str(periodo_obj.get("id")) if periodo_obj else "",
        "estudiante_filtro": estudiante_id,
        "total_boletas": len(boletas),
        "institucion": institucion,
        "rol_actual": rol,
    }
    return render(request, "portal/boletas.html", context)

@login_required
def boletas_export_pdf(request):
    seccion = request.GET.get("seccion", "").strip()
    periodo_id = request.GET.get("periodo_id", "").strip()
    estudiante_id = request.GET.get("estudiante_id", "").strip()

    boletas, periodo_nombre, _, _, _ = get_boletas_data(
        seccion_filtro=seccion,
        periodo_id=periodo_id,
        estudiante_id=estudiante_id
    )
    institucion = ConfiguracionInstitucion.get_activa()
    pdf_bytes = reports.generar_pdf_boletas(boletas, institucion, periodo_nombre=periodo_nombre)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    p_slug = periodo_nombre.replace(' ', '_').replace('í', 'i').replace('Í', 'I')
    sec_slug = f"_{seccion.replace(' ', '_').replace('°', '').replace('-', '_')}" if seccion else ""
    filename = f"Boletas_{p_slug}{sec_slug}.pdf"
    if estudiante_id and boletas:
        est_nombre = boletas[0]["estudiante"].get("nombre_completo", "Estudiante").replace(" ", "_")
        filename = f"Boleta_{est_nombre}_{p_slug}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

@login_required
def boletas_export_excel(request):
    seccion = request.GET.get("seccion", "").strip()
    periodo_id = request.GET.get("periodo_id", "").strip()
    estudiante_id = request.GET.get("estudiante_id", "").strip()

    boletas, periodo_nombre, _, _, _ = get_boletas_data(
        seccion_filtro=seccion,
        periodo_id=periodo_id,
        estudiante_id=estudiante_id
    )
    institucion = ConfiguracionInstitucion.get_activa()
    excel_bytes = reports.generar_excel_boletas(boletas, institucion, periodo_nombre=periodo_nombre)
    response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    p_slug = periodo_nombre.replace(' ', '_').replace('í', 'i').replace('Í', 'I')
    filename = f"Resumen_Boletas_{p_slug}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# ==================== CONSOLIDADOS INSTITUCIONALES ====================
@login_required
def asistencia_consolidado_view(request):
    rol = get_role(request.user)
    estudiantes_raw = api_client.get_estudiantes() or []
    estudiantes_map = {e.get("id"): e for e in estudiantes_raw}
    
    secciones = sorted(list(set([e.get("grado_seccion") for e in estudiantes_raw if e.get("grado_seccion")])))
    
    seccion_filtro = request.GET.get("seccion", "").strip()
    fecha_filtro = request.GET.get("fecha", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()
    
    asistencias_raw = api_client.get_asistencias() or []
    
    registros = []
    for a in asistencias_raw:
        est_id = a.get("estudiante_id")
        est = estudiantes_map.get(est_id, {})
        reg = {
            "id": a.get("id"),
            "estudiante_id": est_id,
            "estudiante_nombre": est.get("nombre_completo", f"Estudiante #{est_id}"),
            "nie": est.get("nie", "---"),
            "grado_seccion": est.get("grado_seccion", "No asignado"),
            "fecha": a.get("fecha"),
            "estado": a.get("estado", "Presente"),
            "observacion": a.get("observacion") or "Sin observaciones",
        }
        
        if seccion_filtro and reg["grado_seccion"] != seccion_filtro:
            continue
        if fecha_filtro and str(reg["fecha"]) != fecha_filtro:
            continue
        if estado_filtro and reg["estado"].lower() != estado_filtro.lower():
            continue
            
        registros.append(reg)
        
    registros.sort(key=lambda r: str(r.get("fecha", "")), reverse=True)
    
    total_registros = len(registros)
    total_presentes = sum(1 for r in registros if r["estado"].lower() == "presente")
    total_ausentes = sum(1 for r in registros if r["estado"].lower() == "ausente")
    total_justificados = sum(1 for r in registros if r["estado"].lower() in ["justificado", "tarde"])
    
    tasa_asistencia = round((total_presentes / total_registros * 100), 1) if total_registros > 0 else 0.0

    context = {
        "registros": registros,
        "secciones": secciones,
        "seccion_filtro": seccion_filtro,
        "fecha_filtro": fecha_filtro,
        "estado_filtro": estado_filtro,
        "total_registros": total_registros,
        "total_presentes": total_presentes,
        "total_ausentes": total_ausentes,
        "total_justificados": total_justificados,
        "tasa_asistencia": tasa_asistencia,
        "rol_actual": rol,
    }
    return render(request, "portal/asistencia_consolidado.html", context)

@login_required
def asistencia_export_pdf(request):
    rol = get_role(request.user)
    estudiantes_raw = api_client.get_estudiantes() or []
    estudiantes_map = {e.get("id"): e for e in estudiantes_raw}
    
    seccion_filtro = request.GET.get("seccion", "").strip()
    fecha_filtro = request.GET.get("fecha", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()
    
    asistencias_raw = api_client.get_asistencias() or []
    
    registros = []
    for a in asistencias_raw:
        est_id = a.get("estudiante_id")
        est = estudiantes_map.get(est_id, {})
        reg = {
            "id": a.get("id"),
            "estudiante_id": est_id,
            "estudiante_nombre": est.get("nombre_completo", f"Estudiante #{est_id}"),
            "nie": est.get("nie", "---"),
            "grado_seccion": est.get("grado_seccion", "No asignado"),
            "fecha": a.get("fecha"),
            "estado": a.get("estado", "Presente"),
            "observacion": a.get("observacion") or "Asistencia regular",
        }
        
        if seccion_filtro and reg["grado_seccion"] != seccion_filtro:
            continue
        if fecha_filtro and str(reg["fecha"]) != fecha_filtro:
            continue
        if estado_filtro and reg["estado"].lower() != estado_filtro.lower():
            continue
            
        registros.append(reg)
        
    registros.sort(key=lambda r: str(r.get("fecha", "")), reverse=True)
    institucion = ConfiguracionInstitucion.get_activa()
    filtros = {
        "seccion": seccion_filtro,
        "fecha": fecha_filtro,
        "estado": estado_filtro
    }
    pdf_bytes = reports.generar_pdf_asistencia(registros, institucion, filtros)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Consolidado_Asistencia.pdf"'
    return response


def get_calificaciones_data(request):
    estudiantes_raw = api_client.get_estudiantes() or []
    estudiantes_map = {e.get("id"): e for e in estudiantes_raw}
    asignaturas_raw = api_client.get_asignaturas() or []
    asignaturas_map = {a.get("id"): a for a in asignaturas_raw}
    periodos_raw = api_client.get_periodos() or []
    periodos_map = {p.get("id"): p for p in periodos_raw}
    secciones_raw = api_client.get_secciones() or []
    
    secciones_set = set([f"{s.get('grado')} - {s.get('seccion')}" for s in secciones_raw if s.get('grado') and s.get('seccion')])
    for e in estudiantes_raw:
        if e.get("grado_seccion"):
            secciones_set.add(e.get("grado_seccion"))
    secciones = sorted(list(secciones_set))
    
    seccion_filtro = request.GET.get("seccion", "").strip()
    asignatura_filtro = request.GET.get("asignatura", "").strip()
    periodo_filtro = request.GET.get("periodo", "").strip()
    
    # Filtrar catálogo canónico de materias (ej: Matemáticas, Ciencias Naturales...)
    if seccion_filtro:
        norm_sec = seccion_filtro.replace("º", "°").lower().strip()
        materias_disponibles = sorted(list(set(
            a.get("nombre") for a in asignaturas_raw
            if a.get("nombre") and (
                not a.get("grado_seccion")
                or a.get("grado_seccion") == "General"
                or norm_sec in a.get("grado_seccion", "").replace("º", "°").lower()
                or a.get("grado_seccion", "").replace("º", "°").lower() in norm_sec
            )
        )))
    else:
        materias_disponibles = sorted(list(set(a.get("nombre") for a in asignaturas_raw if a.get("nombre"))))

    # Si la materia seleccionada no está disponible para la sección elegida, limpiar filtro
    if asignatura_filtro and asignatura_filtro not in materias_disponibles and not any(str(a.get("id")) == str(asignatura_filtro) for a in asignaturas_raw):
        asignatura_filtro = ""

    asignaturas_disponibles = [a for a in asignaturas_raw if not asignatura_filtro or a.get("nombre") == asignatura_filtro or str(a.get("id")) == asignatura_filtro]

    calificaciones_raw = api_client.get_calificaciones() or []
    
    registros = []
    for c in calificaciones_raw:
        est_id = c.get("estudiante_id")
        asig_id = c.get("asignatura_id")
        per_id = c.get("periodo_id")
        
        est = estudiantes_map.get(est_id, {})
        asig = asignaturas_map.get(asig_id, {})
        per = periodos_map.get(per_id, {})
        
        nota = float(c.get("nota", 0.0))
        reg = {
            "id": c.get("id"),
            "estudiante_id": est_id,
            "estudiante_nombre": est.get("nombre_completo", f"Estudiante #{est_id}"),
            "nie": est.get("nie", "---"),
            "grado_seccion": est.get("grado_seccion", "No asignado"),
            "asignatura_id": asig_id,
            "asignatura_nombre": asig.get("nombre", f"Materia #{asig_id}"),
            "asignatura_codigo": asig.get("codigo", ""),
            "profesor_nombre": asig.get("profesor_nombre", "Docente asignado"),
            "periodo_id": per_id,
            "periodo_nombre": per.get("nombre", f"Período #{per_id}"),
            "tipo_evaluacion": c.get("tipo_evaluacion", "Evaluación General"),
            "nota": nota,
            "aprobado": nota >= 6.0,
        }
        
        if seccion_filtro and reg["grado_seccion"] != seccion_filtro:
            continue
        if asignatura_filtro:
            # Filtrar por nombre canónico ("Matemáticas") o por id específico
            if reg["asignatura_nombre"].strip().lower() != asignatura_filtro.strip().lower() and str(reg["asignatura_id"]) != asignatura_filtro:
                continue
        if periodo_filtro and str(reg["periodo_id"]) != periodo_filtro:
            continue
            
        registros.append(reg)
    
    return registros, secciones, materias_disponibles, periodos_raw, seccion_filtro, asignatura_filtro, periodo_filtro, asignaturas_raw

@login_required
def calificaciones_consolidado_view(request):
    rol = get_role(request.user)
    registros, secciones, materias_disponibles, periodos_raw, seccion_filtro, asignatura_filtro, periodo_filtro, todas_asignaturas = get_calificaciones_data(request)
    
    total_evaluados = len(registros)
    suma_notas = sum(r["nota"] for r in registros)
    promedio_general = round((suma_notas / total_evaluados), 2) if total_evaluados > 0 else 0.0
    total_aprobados = sum(1 for r in registros if r["aprobado"])
    total_reprobados = total_evaluados - total_aprobados
    tasa_aprobacion = round((total_aprobados / total_evaluados * 100), 1) if total_evaluados > 0 else 0.0

    context = {
        "registros": registros,
        "secciones": secciones,
        "materias": materias_disponibles,
        "asignaturas": materias_disponibles,
        "todas_asignaturas": todas_asignaturas,
        "periodos": periodos_raw,
        "seccion_filtro": seccion_filtro,
        "asignatura_filtro": asignatura_filtro,
        "periodo_filtro": periodo_filtro,
        "total_evaluados": total_evaluados,
        "promedio_general": promedio_general,
        "total_aprobados": total_aprobados,
        "total_reprobados": total_reprobados,
        "tasa_aprobacion": tasa_aprobacion,
        "rol_actual": rol,
    }
    return render(request, "portal/calificaciones_consolidado.html", context)

@login_required
def calificaciones_export_pdf(request):
    registros, _, asignaturas, periodos, seccion_filtro, asignatura_filtro, periodo_filtro, _ = get_calificaciones_data(request)
    institucion = ConfiguracionInstitucion.get_activa()

    asig_nombre = next((a.get("nombre") for a in asignaturas if str(a.get("id")) == asignatura_filtro), "")
    per_nombre = next((p.get("nombre") for p in periodos if str(p.get("id")) == periodo_filtro), "")

    filtros = {
        "seccion": seccion_filtro,
        "asignatura": asig_nombre,
        "periodo": per_nombre,
    }
    pdf_bytes = reports.generar_pdf_calificaciones(registros, institucion, filtros)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="Consolidado_Calificaciones.pdf"'
    return response

@login_required
def calificaciones_export_excel(request):
    registros, _, _, _, _, _, _, _ = get_calificaciones_data(request)
    institucion = ConfiguracionInstitucion.get_activa()
    excel_bytes = reports.generar_excel_calificaciones(registros, institucion)
    response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Consolidado_Calificaciones.xlsx"'
    return response


@login_required
def ajustes_view(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Los ajustes solo pueden ser editados por el Director.")
        return redirect('dashboard')

    institucion = ConfiguracionInstitucion.get_activa()
    if request.method == 'POST':
        institucion.nombre = request.POST.get('nombre', institucion.nombre).strip()
        institucion.codigo_mined = request.POST.get('codigo_mined', institucion.codigo_mined).strip()
        institucion.anio_lectivo = request.POST.get('anio_lectivo', institucion.anio_lectivo).strip()
        institucion.regimen = request.POST.get('regimen', institucion.regimen).strip()
        institucion.director_nombre = request.POST.get('director_nombre', institucion.director_nombre).strip()
        institucion.direccion = request.POST.get('direccion', institucion.direccion).strip()
        institucion.telefono = request.POST.get('telefono', institucion.telefono).strip()

        if request.POST.get('eliminar_logo') == '1':
            if institucion.logo:
                institucion.logo.delete(save=False)
                institucion.logo = None
        elif 'logo' in request.FILES:
            institucion.logo = request.FILES['logo']

        institucion.save()
        messages.success(request, "¡Ajustes institucionales guardados con éxito!")
        return redirect('ajustes_view')

    return render(request, "portal/ajustes.html", {"institucion": institucion})

# ==================== GESTIÓN Y AUTORIZACIÓN DE USUARIOS ====================
@login_required
def usuarios_list(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo el Director General puede administrar y autorizar usuarios.")
        return redirect('dashboard')

    usuarios = api_client.get_usuarios()
    context = {
        "usuarios": usuarios,
        "total": len(usuarios),
        "rol_actual": rol,
    }
    return render(request, "portal/usuarios.html", context)

@login_required
def usuario_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo el Director puede registrar usuarios.")
        return redirect('dashboard')

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        correo = request.POST.get("correo", "").strip().lower()
        password = request.POST.get("password", "").strip()
        rol_nuevo = request.POST.get("rol", "Profesor").strip()

        if not nombre or not correo or not password:
            messages.error(request, "Todos los campos (nombre, correo y contraseña) son obligatorios.")
            return redirect('usuarios_list')

        data = {
            "nombre": nombre,
            "correo": correo,
            "password": password,
            "rol": rol_nuevo,
            "estado": True
        }
        success, res = api_client.create_usuario(data)
        if success:
            # Sincronizar en Django User para acceso al portal web
            from django.contrib.auth.models import User
            dj_user, created = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
            dj_user.set_password(password)
            dj_user.save()
            PerfilUsuario.objects.update_or_create(user=dj_user, defaults={"rol": rol_nuevo})
            messages.success(request, f"¡Usuario '{nombre}' ({rol_nuevo}) creado y autorizado exitosamente!")
        else:
            messages.error(request, f"Error al crear usuario: {res}")

    return redirect('usuarios_list')

@login_required
def usuario_toggle_estado(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo el Director puede autorizar o desautorizar usuarios.")
        return redirect('dashboard')

    if request.method == "POST":
        usuarios = api_client.get_usuarios()
        target = next((u for u in usuarios if u.get("id") == id), None)
        if api_client.toggle_usuario_estado(id):
            if target:
                correo = target.get("correo")
                from django.contrib.auth.models import User
                dj_user = User.objects.filter(email__iexact=correo).first() or User.objects.filter(username__iexact=correo).first()
                if dj_user:
                    dj_user.is_active = not target.get("estado", True)
                    dj_user.save()
            messages.success(request, "Estado de autorización actualizado correctamente.")
        else:
            messages.error(request, "No se pudo actualizar el estado del usuario.")

    return redirect('usuarios_list')

@login_required
def usuario_update_password(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo el Director puede restablecer contraseñas.")
        return redirect('dashboard')

    if request.method == "POST":
        nueva_pass = request.POST.get("password", "").strip()
        if not nueva_pass:
            messages.error(request, "La contraseña no puede estar vacía.")
            return redirect('usuarios_list')

        usuarios = api_client.get_usuarios()
        target = next((u for u in usuarios if u.get("id") == id), None)
        if api_client.update_usuario_password(id, nueva_pass):
            if target:
                correo = target.get("correo")
                from django.contrib.auth.models import User
                dj_user = User.objects.filter(email__iexact=correo).first() or User.objects.filter(username__iexact=correo).first()
                if dj_user:
                    dj_user.set_password(nueva_pass)
                    dj_user.save()
            messages.success(request, "¡Contraseña actualizada con éxito!")
        else:
            messages.error(request, "No se pudo actualizar la contraseña.")

    return redirect('usuarios_list')

@login_required
def usuario_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo el Director puede eliminar usuarios.")
        return redirect('dashboard')

    if request.method == "POST":
        usuarios = api_client.get_usuarios()
        target = next((u for u in usuarios if u.get("id") == id), None)
        if api_client.delete_usuario(id):
            if target:
                correo = target.get("correo")
                from django.contrib.auth.models import User
                User.objects.filter(email__iexact=correo).delete()
                User.objects.filter(username__iexact=correo).delete()
            messages.success(request, "Usuario eliminado correctamente.")
        else:
            messages.error(request, "No se pudo eliminar el usuario.")

    return redirect('usuarios_list')

# ==================== AULAS Y HORARIOS ====================
@login_required
def aulas_horarios_view(request):
    rol = get_role(request.user)
    
    # Parámetros de filtro y pestaña activa
    active_tab = request.GET.get('tab', 'seccion')
    if active_tab == 'horarios':
        active_tab = 'seccion'

    seccion_id_str = request.GET.get('seccion_id', '')
    profesor_id_str = request.GET.get('profesor_id', '')

    seccion_id = int(seccion_id_str) if seccion_id_str.isdigit() else None
    profesor_id = int(profesor_id_str) if profesor_id_str.isdigit() else None

    aulas = api_client.get_aulas()
    secciones = api_client.get_secciones()
    profesores = api_client.get_profesores()
    asignaturas = api_client.get_asignaturas()
    anios = api_client.get_anios()

    import re
    def _calc_sec_key(texto):
        if not texto: return ""
        num = re.findall(r'\d+', str(texto))
        n = num[0] if num else ""
        l_match = re.search(r'secci[oó]n\s*([a-zA-Z])', str(texto), re.I)
        if not l_match:
            l_match = re.search(r'[\s\-\(]([a-zA-Z])[\)\s]?$', str(texto), re.I)
        l = (l_match.group(1) if l_match else "").upper()
        return f"{n}_{l}"

    # Asignar sec_key a cada sección
    for s in secciones:
        s['sec_key'] = _calc_sec_key(f"{s.get('grado', '')} {s.get('seccion', '')}")

    # Mapeo de profesores por nombre a su ID
    prof_map = {}
    for p in profesores:
        nom = p.get('nombre', '').strip().lower()
        clean = re.sub(r'^(lic\.|prof\.|ing\.)\s*', '', nom).strip()
        prof_map[clean] = str(p.get('id'))

    # Asignar profesor_id y sec_key a cada asignatura
    for a in asignaturas:
        a['sec_key'] = _calc_sec_key(a.get('grado_seccion', ''))
        nom_p = a.get('profesor_nombre', '').strip().lower()
        clean_p = re.sub(r'^(lic\.|prof\.|ing\.)\s*', '', nom_p).strip()
        pid = prof_map.get(clean_p)
        if not pid:
            for k, v in prof_map.items():
                if k in clean_p or clean_p in k:
                    pid = v
                    break
        a['profesor_id'] = pid or ""

    # Organizar secciones por ciclo para selector visual rápido
    ciclos_secciones = [
        {
            "ciclo": "Tercer Ciclo (7º a 9º Grado)",
            "ciclo_id": "c3",
            "secciones": [s for s in secciones if any(g in s.get("grado", "") for g in ["7", "8", "9"])]
        },
        {
            "ciclo": "Segundo Ciclo (4º a 6º Grado)",
            "ciclo_id": "c2",
            "secciones": [s for s in secciones if any(g in s.get("grado", "") for g in ["4", "5", "6"])]
        },
        {
            "ciclo": "Primer Ciclo (1º a 3º Grado)",
            "ciclo_id": "c1",
            "secciones": [s for s in secciones if any(g in s.get("grado", "") for g in ["1", "2", "3"])]
        },
    ]

    # Preseleccionar sección o profesor según la pestaña
    if active_tab == 'seccion':
        if seccion_id is None and secciones:
            s_default = next((s for s in secciones if "7" in s.get("grado", "") and "A" in s.get("seccion", "")), secciones[0])
            seccion_id = s_default.get('id')
        horarios = api_client.get_horarios(grado_seccion_id=seccion_id)
    elif active_tab == 'docente':
        if profesor_id is None and profesores:
            profesor_id = profesores[0].get('id')
        horarios = api_client.get_horarios(profesor_id=profesor_id)
    else:  # 'aulas'
        horarios = []

    # Agrupar horarios por día de la semana
    dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    horarios_por_dia = {d: [] for d in dias}
    for h in horarios:
        d = h.get("dia_semana", "Lunes")
        if "iercol" in d.lower():
            d = "Miercoles"
        if d in horarios_por_dia:
            horarios_por_dia[d].append(h)

    # Ordenar bloques de cada día cronológicamente
    for d in dias:
        horarios_por_dia[d].sort(key=lambda x: str(x.get("hora_inicio", "")))

    # Entidades actuales
    seccion_actual = next((s for s in secciones if s.get('id') == seccion_id), None)
    profesor_actual = next((p for p in profesores if p.get('id') == profesor_id), None)

    # Separar aulas base (estándar) y aulas especiales (laboratorios, talleres, canchas)
    aulas_especiales = [a for a in aulas if a.get('tipo') not in ['Estandar', 'Teorica', None, '']]
    aulas_estandar = [a for a in aulas if a.get('tipo') in ['Estandar', 'Teorica', None, '']]

    context = {
        "rol_actual": rol,
        "aulas": aulas,
        "aulas_especiales": aulas_especiales,
        "aulas_estandar": aulas_estandar,
        "secciones": secciones,
        "ciclos_secciones": ciclos_secciones,
        "profesores": profesores,
        "asignaturas": asignaturas,
        "anios": anios,
        "horarios": horarios,
        "horarios_por_dia": horarios_por_dia,
        "dias": dias,
        "seccion_id": seccion_id,
        "profesor_id": profesor_id,
        "seccion_actual": seccion_actual,
        "profesor_actual": profesor_actual,
        "active_tab": active_tab,
        "total_aulas": len(aulas),
        "total_secciones": len(secciones),
        "total_clases_vista": len(horarios),
        "total_horarios": len(horarios),
    }
    return render(request, "portal/horarios.html", context)

@login_required
def horario_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede programar la carga horaria.")
        return redirect('horarios_view')

    if request.method == "POST":
        gs_id = request.POST.get("grado_seccion_id")
        m_id = request.POST.get("materia_id")
        p_id = request.POST.get("profesor_id")
        anio_id = request.POST.get("anio_lectivo_id") or 1
        dia = request.POST.get("dia_semana")
        hora_ini = request.POST.get("hora_inicio")
        hora_fin = request.POST.get("hora_fin")
        aula_esp = request.POST.get("aula_especial_id") or None

        if not (gs_id and m_id and p_id and dia and hora_ini and hora_fin):
            messages.error(request, "Todos los campos de materia, docente, sección, día y bloque horario son requeridos.")
            return redirect(f"/horarios/?seccion_id={gs_id}")

        data = {
            "grado_seccion_id": int(gs_id),
            "materia_id": int(m_id),
            "profesor_id": int(p_id),
            "anio_lectivo_id": int(anio_id),
            "dia_semana": dia,
            "hora_inicio": hora_ini,
            "hora_fin": hora_fin,
            "aula_especial_id": int(aula_esp) if aula_esp and aula_esp.isdigit() else None
        }

        success, res = api_client.create_horario(data)
        if success:
            messages.success(request, "¡Bloque horario asignado exitosamente!")
        else:
            messages.error(request, f"Conflicto de Horario: {res}")

        return redirect(f"/horarios/?seccion_id={gs_id}")

    return redirect('horarios_view')

@login_required
def horario_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede eliminar bloques de horario.")
        return redirect('horarios_view')

    seccion_id = request.POST.get("seccion_id", "")
    if request.method == "POST":
        success, res = api_client.delete_horario(id)
        if success:
            messages.success(request, "Bloque horario eliminado correctamente.")
        else:
            messages.error(request, f"No se pudo eliminar el bloque: {res}")

    url = f"/horarios/?seccion_id={seccion_id}" if seccion_id else "/horarios/"
    return redirect(url)

@login_required
def aula_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo Dirección General puede administrar infraestructura y aulas.")
        return redirect('horarios_view')

    if request.method == "POST":
        codigo = request.POST.get("codigo", "").strip().upper()
        nombre = request.POST.get("nombre", "").strip()
        tipo = request.POST.get("tipo", "Estandar")
        capacidad = request.POST.get("capacidad")
        ubicacion = request.POST.get("ubicacion", "").strip()

        if not codigo or not nombre:
            messages.error(request, "Código y nombre de aula son obligatorios.")
            return redirect('/horarios/?tab=aulas')

        data = {
            "codigo": codigo,
            "nombre": nombre,
            "tipo": tipo,
            "capacidad": int(capacidad) if capacidad and capacidad.isdigit() else 35,
            "ubicacion": ubicacion or None,
            "estado": True
        }
        success, res = api_client.create_aula(data)
        if success:
            messages.success(request, f"¡Aula '{nombre}' ({codigo}) registrada con éxito!")
        else:
            messages.error(request, f"Error al registrar aula: {res}")

    return redirect('/horarios/?tab=aulas')

@login_required
def aula_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo la Dirección General puede eliminar aulas.")
        return redirect('horarios_view')

    if request.method == "POST":
        success, res = api_client.delete_aula(id)
        if success:
            messages.success(request, "Aula eliminada correctamente del inventario.")
        else:
            messages.error(request, f"No se pudo eliminar el aula: {res}")

    return redirect('/horarios/?tab=aulas')

@login_required
def seccion_create(request):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo Dirección puede habilitar nuevas secciones para el ciclo lectivo.")
        return redirect('horarios_view')

    if request.method == "POST":
        grado = request.POST.get("grado", "").strip()
        seccion = request.POST.get("seccion", "").strip().upper()
        anio = request.POST.get("anio_lectivo")
        aula_base = request.POST.get("aula_base_id")

        if not grado or not seccion or not anio:
            messages.error(request, "Grado, sección y año lectivo son obligatorios.")
            return redirect('/horarios/?tab=secciones')

        data = {
            "grado": grado,
            "seccion": seccion,
            "anio_lectivo": int(anio),
            "aula_base_id": int(aula_base) if aula_base and aula_base.isdigit() else None
        }
        success, res = api_client.create_seccion(data)
        if success:
            messages.success(request, f"¡Sección '{grado} {seccion}' habilitada para el año lectivo {anio}!")
        else:
            messages.error(request, f"Error al crear sección: {res}")

    return redirect('/horarios/?tab=secciones')

@login_required
def seccion_asignar_aula(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso Denegado: Solo Dirección puede asignar aulas base a secciones.")
        return redirect('horarios_view')

    if request.method == "POST":
        aula_base_id = request.POST.get("aula_base_id")
        ab_id = int(aula_base_id) if aula_base_id and aula_base_id.isdigit() else None
        success, res = api_client.update_seccion_aula(id, ab_id)
        if success:
            messages.success(request, "¡Aula base asignada exitosamente a la sección!")
        else:
            messages.error(request, f"Conflicto de asignación: {res}")

    return redirect('/horarios/?tab=secciones')



