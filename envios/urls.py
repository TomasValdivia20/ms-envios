from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehiculoViewSet, RepartidorViewSet, RutaViewSet, EnvioViewSet

# Instanciamos el router
router = DefaultRouter()

# Registramos nuestros endpoints principales
router.register(r'vehiculos', VehiculoViewSet)
router.register(r'repartidores', RepartidorViewSet)
router.register(r'rutas', RutaViewSet)
router.register(r'envios', EnvioViewSet)

urlpatterns = [
    # Incluimos todas las rutas generadas mágicamente por el router
    path('', include(router.urls)),
]