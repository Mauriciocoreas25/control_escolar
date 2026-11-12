import requests
from django.conf import settings

BASE_URL = getattr(settings, 'API_BASE_URL', 'http://127.0.0.1:8001')

# ==================== ESTUDIANTES ====================
def get_estudiantes():
    try:
        r = requests.get(f"{BASE_URL}/estudiantes/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_estudiantes: {e}")
    return []

def get_estudiante(estudiante_id):
    try:
        estudiantes = get_estudiantes()
        for e in estudiantes:
            if e.get("id") == estudiante_id:
                return e
    except Exception as e:
        print(f"[API ERROR] get_estudiante: {e}")
    return None

def create_estudiante(data):
    try:
        r = requests.post(f"{BASE_URL}/estudiantes/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def update_estudiante(estudiante_id, data):
    try:
        r = requests.patch(f"{BASE_URL}/estudiantes/{estudiante_id}", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def delete_estudiante(estudiante_id):
    try:
        r = requests.delete(f"{BASE_URL}/estudiantes/{estudiante_id}", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] delete_estudiante: {e}")
        return False

# ==================== PROFESORES / DOCENTES ====================
def get_profesores():
    try:
        r = requests.get(f"{BASE_URL}/profesores/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_profesores: {e}")
    return []

def create_profesor(data):
    try:
        r = requests.post(f"{BASE_URL}/profesores/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def delete_profesor(profesor_id):
    try:
        r = requests.delete(f"{BASE_URL}/profesores/{profesor_id}", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] delete_profesor: {e}")
        return False

# ==================== ASIGNATURAS ====================
def get_asignaturas():
    try:
        r = requests.get(f"{BASE_URL}/asignaturas/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_asignaturas: {e}")
    return []

def create_asignatura(data):
    try:
        r = requests.post(f"{BASE_URL}/asignaturas/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def update_asignatura(asignatura_id, data):
    try:
        r = requests.patch(f"{BASE_URL}/asignaturas/{asignatura_id}", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def delete_asignatura(asignatura_id):
    try:
        r = requests.delete(f"{BASE_URL}/asignaturas/{asignatura_id}", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] delete_asignatura: {e}")
        return False

# ==================== AÑOS LECTIVOS (CICLOS) ====================
def get_anios():
    try:
        r = requests.get(f"{BASE_URL}/anios-lectivos/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_anios: {e}")
    return []

def create_anio(data):
    try:
        r = requests.post(f"{BASE_URL}/anios-lectivos/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def delete_anio(anio_id):
    try:
        r = requests.delete(f"{BASE_URL}/anios-lectivos/{anio_id}", timeout=3)
        if r.status_code == 200:
            return True, "Ciclo escolar eliminado exitosamente."
        detail = r.json().get("detail", "No se pudo eliminar el ciclo.") if r.headers.get("content-type") == "application/json" else r.text
        return False, detail
    except Exception as e:
        print(f"[API ERROR] delete_anio: {e}")
        return False, str(e)

def toggle_anio_estado(anio_id, nuevo_estado):
    try:
        payload = {"estado": nuevo_estado}
        r = requests.patch(f"{BASE_URL}/anios-lectivos/{anio_id}/estado", json=payload, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] toggle_anio_estado: {e}")
        return False


# ==================== PERIODOS ESCOLARES ====================
def get_periodos():
    try:
        r = requests.get(f"{BASE_URL}/periodos/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_periodos: {e}")
    return []

def create_periodo(data):
    try:
        r = requests.post(f"{BASE_URL}/periodos/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def delete_periodo(periodo_id):
    try:
        r = requests.delete(f"{BASE_URL}/periodos/{periodo_id}", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] delete_periodo: {e}")
        return False

def toggle_periodo(periodo_id, nombre, anio_lectivo_id, nuevo_estado):
    try:
        payload = {
            "nombre": nombre,
            "anio_lectivo_id": anio_lectivo_id,
            "estado": nuevo_estado
        }
        r = requests.patch(f"{BASE_URL}/periodos/{periodo_id}", json=payload, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] toggle_periodo: {e}")
        return False

# ==================== USUARIOS Y AUTENTICACIÓN ====================
def api_login(correo, password):
    try:
        payload = {"correo": correo, "password": password}
        r = requests.post(f"{BASE_URL}/auth/login", json=payload, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.json().get("detail", "Error de autenticación")
    except Exception as e:
        return False, str(e)

def get_usuarios():
    try:
        r = requests.get(f"{BASE_URL}/usuarios/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_usuarios: {e}")
    return []

def create_usuario(data):
    try:
        r = requests.post(f"{BASE_URL}/usuarios/", json=data, timeout=3)
        return r.status_code == 200, r.json() if r.status_code == 200 else r.json().get("detail", "Error al crear usuario")
    except Exception as e:
        return False, str(e)

def toggle_usuario_estado(usuario_id):
    try:
        r = requests.patch(f"{BASE_URL}/usuarios/{usuario_id}/toggle-estado", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] toggle_usuario_estado: {e}")
        return False

def update_usuario_password(usuario_id, password):
    try:
        payload = {"password": password}
        r = requests.patch(f"{BASE_URL}/usuarios/{usuario_id}/password", json=payload, timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] update_usuario_password: {e}")
        return False

def delete_usuario(usuario_id):
    try:
        r = requests.delete(f"{BASE_URL}/usuarios/{usuario_id}", timeout=3)
        return r.status_code == 200
    except Exception as e:
        print(f"[API ERROR] delete_usuario: {e}")
        return False

# ==================== ASISTENCIAS Y CALIFICACIONES ====================
def get_asistencias():
    try:
        r = requests.get(f"{BASE_URL}/asistencias/", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_asistencias: {e}")
    return []

def get_actividades(asignatura_id=None, periodo_id=None):
    try:
        params = {}
        if asignatura_id:
            params["asignatura_id"] = asignatura_id
        if periodo_id:
            params["periodo_id"] = periodo_id
        r = requests.get(f"{BASE_URL}/actividades/", params=params, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_actividades: {e}")
    return []

def get_calificaciones(asignatura_id=None, periodo_id=None, estudiante_id=None):
    try:
        params = {}
        if asignatura_id:
            params["asignatura_id"] = asignatura_id
        if periodo_id:
            params["periodo_id"] = periodo_id
        if estudiante_id:
            params["estudiante_id"] = estudiante_id
        r = requests.get(f"{BASE_URL}/calificaciones/", params=params, timeout=4)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_calificaciones: {e}")
    return []

# ==================== AULAS ====================
def get_aulas(tipo=None, estado=None):
    try:
        params = {}
        if tipo:
            params["tipo"] = tipo
        if estado is not None:
            params["estado"] = estado
        r = requests.get(f"{BASE_URL}/aulas/", params=params, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_aulas: {e}")
    return []

def create_aula(data):
    try:
        r = requests.post(f"{BASE_URL}/aulas/", json=data, timeout=3)
        if r.status_code in [200, 201]:
            return True, r.json()
        detail = r.json().get("detail", "Error al crear aula") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

def update_aula(aula_id, data):
    try:
        r = requests.patch(f"{BASE_URL}/aulas/{aula_id}", json=data, timeout=3)
        if r.status_code == 200:
            return True, r.json()
        detail = r.json().get("detail", "Error al actualizar aula") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

def delete_aula(aula_id):
    try:
        r = requests.delete(f"{BASE_URL}/aulas/{aula_id}", timeout=3)
        if r.status_code == 200:
            return True, r.json().get("mensaje", "Aula eliminada")
        detail = r.json().get("detail", "No se pudo eliminar el aula") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

# ==================== SECCIONES ====================
def get_secciones(anio_lectivo=None):
    try:
        params = {}
        if anio_lectivo:
            params["anio_lectivo"] = anio_lectivo
        r = requests.get(f"{BASE_URL}/secciones/", params=params, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_secciones: {e}")
    return []

def create_seccion(data):
    try:
        r = requests.post(f"{BASE_URL}/secciones/", json=data, timeout=3)
        if r.status_code in [200, 201]:
            return True, r.json()
        detail = r.json().get("detail", "Error al crear sección") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

def update_seccion_aula(seccion_id, aula_base_id):
    try:
        params = {}
        if aula_base_id is not None:
            params["aula_base_id"] = aula_base_id
        r = requests.patch(f"{BASE_URL}/secciones/{seccion_id}/aula-base", params=params, timeout=3)
        if r.status_code == 200:
            return True, r.json()
        detail = r.json().get("detail", "Error al asignar aula base") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

# ==================== HORARIOS ====================
def get_horarios(grado_seccion_id=None, profesor_id=None, dia_semana=None, anio_lectivo_id=None):
    try:
        params = {}
        if grado_seccion_id:
            params["grado_seccion_id"] = grado_seccion_id
        if profesor_id:
            params["profesor_id"] = profesor_id
        if dia_semana:
            params["dia_semana"] = dia_semana
        if anio_lectivo_id:
            params["anio_lectivo_id"] = anio_lectivo_id
        r = requests.get(f"{BASE_URL}/horarios/", params=params, timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"[API ERROR] get_horarios: {e}")
    return []

def create_horario(data):
    try:
        r = requests.post(f"{BASE_URL}/horarios/", json=data, timeout=3)
        if r.status_code in [200, 201]:
            return True, r.json()
        detail = r.json().get("detail", "Error al crear horario") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)

def delete_horario(horario_id):
    try:
        r = requests.delete(f"{BASE_URL}/horarios/{horario_id}", timeout=3)
        if r.status_code == 200:
            return True, r.json().get("mensaje", "Horario eliminado")
        detail = r.json().get("detail", "No se pudo eliminar el horario") if r.headers.get("content-type", "").startswith("application/json") else r.text
        return False, detail
    except Exception as e:
        return False, str(e)


