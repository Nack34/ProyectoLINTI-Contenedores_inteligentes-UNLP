from .auth import login_api, logout_api, signup_api, DecoratedTokenRefreshView
from .residuos import reclamar_residuo, total_residuos, total_residuos_por_usuario
from .estaciones import get_ubicacion_estacion, get_ubicacion_estaciones
from .ranking import get_ranking, get_posicion_ranking, get_puntos_usuario