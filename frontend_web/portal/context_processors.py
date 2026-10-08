from .models import ConfiguracionInstitucion

def institucion_context(request):
    try:
        institucion = ConfiguracionInstitucion.get_activa()
    except Exception:
        institucion = None

    user_rol = None
    if request.user.is_authenticated:
        if hasattr(request.user, 'perfil'):
            user_rol = request.user.perfil.rol
        elif request.user.is_superuser:
            user_rol = 'Director'

    return {
        'institucion': institucion,
        'user_rol': user_rol,
    }
