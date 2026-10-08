from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .services import api_client
from .models import ConfiguracionInstitucion, PerfilUsuario

def get_role(user):
    if not user.is_authenticated:
        return None
    if hasattr(user, 'perfil'):
        return user.perfil.rol
    if user.is_superuser:
        return 'Director'
    return 'Secretaria'

# ==================== AUTENTICACIÓN ====================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '').strip()

        # Soporte para ingresar nombre de usuario o correo institucional
        username_to_auth = u
        if u.lower() in ['director@santabartolome.edu.sv', 'director']:
            username_to_auth = 'director'
        elif u.lower() in ['secretaria@santabartolome.edu.sv', 'secretaria']:
            username_to_auth = 'secretaria'

        user = authenticate(request, username=username_to_auth, password=p)

        if user is not None:
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
    messages.info(request, "Has cerrado sesión correctamente.")
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
                "vigencia": "Ciclo Escolar Activo",
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
def estudiante_create(request):
    rol = get_role(request.user)
    if rol != 'Secretaria':
        messages.error(request, "Acceso Denegado: La matrícula es responsabilidad exclusiva de Secretaría.")
        return redirect('estudiantes_list')

    if request.method == "POST":
        nie = request.POST.get("nie", "").strip()
        nombre_completo = request.POST.get("nombre_completo", "").strip()
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
            "telefono": telefono
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
    if rol != 'Secretaria':
        messages.error(request, "Acceso Denegado: Solo Secretaría puede modificar expedientes.")
        return redirect('estudiantes_list')

    if request.method == "POST":
        data = {
            "nie": request.POST.get("nie", "").strip(),
            "nombre_completo": request.POST.get("nombre_completo", "").strip(),
            "grado_seccion": request.POST.get("grado_seccion", "").strip(),
            "encargado": request.POST.get("encargado", "").strip(),
            "telefono": request.POST.get("telefono", "").strip()
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
    if rol != 'Secretaria':
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
        correo = request.POST.get("correo", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        especialidad = request.POST.get("especialidad", "").strip()

        if not nombre or not correo:
            messages.error(request, "Nombre y Correo electrónico son obligatorios.")
            return redirect("docentes_list")

        data = {
            "nombre": nombre,
            "correo": correo,
            "telefono": telefono,
            "especialidad": especialidad,
            "password": "docente123"
        }
        success, res = api_client.create_profesor(data)
        if success:
            messages.success(request, f"Docente {nombre} registrado exitosamente.")
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
        if api_client.delete_profesor(id):
            messages.success(request, "Docente eliminado correctamente.")
        else:
            messages.error(request, "No se pudo eliminar el docente.")
    return redirect("docentes_list")

# ==================== ASIGNATURAS / CARGA ACADÉMICA ====================
@login_required
def carga_academica(request):
    asignaturas = api_client.get_asignaturas()
    profesores = api_client.get_profesores()
    rol = get_role(request.user)
    context = {
        "asignaturas": asignaturas,
        "profesores": profesores,
        "total": len(asignaturas),
        "rol_actual": rol,
    }
    return render(request, "portal/carga_academica.html", context)

@login_required
def asignatura_create(request):
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
        success, res = api_client.create_asignatura(data)
        if success:
            messages.success(request, f"¡Asignatura '{nombre}' ({codigo}) registrada con éxito!")
        else:
            messages.error(request, "Error: El código de asignatura ya está en uso.")

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
        messages.error(request, "Solo la Dirección General puede crear nuevos ciclos escolares.")
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
            messages.success(request, f"¡Ciclo escolar {anio} creado con éxito!")
        else:
            messages.error(request, "El ciclo escolar ya se encuentra registrado.")

    return redirect("periodos_list")

@login_required
def anio_delete(request, id):
    rol = get_role(request.user)
    if rol != 'Director':
        messages.error(request, "Acceso denegado.")
        return redirect("periodos_list")

    if request.method == "POST":
        if api_client.delete_anio(id):
            messages.success(request, "Ciclo escolar eliminado.")
        else:
            messages.error(request, "No se pudo eliminar el ciclo.")
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
        messages.error(request, "Acceso Denegado: El bloqueo de períodos lectivos es potestad exclusiva del Director.")
        return redirect('periodos_list')

    if request.method == "POST":
        periodos = api_client.get_periodos()
        target = next((p for p in periodos if p.get("id") == id), None)
        if target:
            nuevo_estado = "Cerrado" if target.get("estado") == "Abierto" else "Abierto"
            ok = api_client.toggle_periodo(
                id,
                target.get("nombre", "Trimestre"),
                target.get("anio_lectivo_id", 1),
                nuevo_estado
            )
            if ok:
                if nuevo_estado == "Cerrado":
                    messages.success(request, f"¡Período '{target.get('nombre')}' CERRADO Y BLOQUEADO!")
                else:
                    messages.success(request, f"¡Período '{target.get('nombre')}' REABIERTO!")
            else:
                messages.error(request, "Error al actualizar estado en la API.")
    return redirect('periodos_list')

# ==================== BOLETAS Y AJUSTES ====================
@login_required
def boletas_view(request):
    estudiantes = api_client.get_estudiantes()
    periodos = api_client.get_periodos()
    return render(request, "portal/boletas.html", {"estudiantes": estudiantes, "periodos": periodos})

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
        if api_client.toggle_usuario_estado(id):
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

        if api_client.update_usuario_password(id, nueva_pass):
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
        if api_client.delete_usuario(id):
            messages.success(request, "Usuario eliminado correctamente.")
        else:
            messages.error(request, "No se pudo eliminar el usuario.")

    return redirect('usuarios_list')

