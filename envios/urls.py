from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehiculoViewSet, RepartidorViewSet, RutaViewSet, EnvioViewSet, calcular_costos

router = DefaultRouter()

router.register(r'vehiculos', VehiculoViewSet)
router.register(r'repartidores', RepartidorViewSet)
router.register(r'rutas', RutaViewSet)
router.register(r'envios', EnvioViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('calcular-costos/', calcular_costos, name='calcular-costos'),
]