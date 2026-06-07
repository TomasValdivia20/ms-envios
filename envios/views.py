from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vehiculo, Repartidor, Ruta, Envio
from .services import OptimizadorRutasService
from .serializers import (
    VehiculoSerializer, 
    RepartidorSerializer, 
    RutaSerializer, 
    EnvioSerializer
)

class VehiculoViewSet(viewsets.ModelViewSet):
    """
    Gestiona el CRUD de los vehículos de la flota de SmartLogix.
    """
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer

class RepartidorViewSet(viewsets.ModelViewSet):
    """
    Gestiona la información de los repartidores y sus estados.
    """
    queryset = Repartidor.objects.all()
    serializer_class = RepartidorSerializer

class RutaViewSet(viewsets.ModelViewSet):
    """
    Gestiona la planificación y seguimiento de las rutas de despacho.
    Incluye las paradas anidadas gracias a su serializer.
    """
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer

class EnvioViewSet(viewsets.ModelViewSet):
    """
    Controla cada paquete o envío individual de la logística.
    """
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer
    
    
class RutaViewSet(viewsets.ModelViewSet):
    """
    Gestiona la planificación y seguimiento de las rutas de despacho.
    """
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer

    # NUEVO ENDPOINT PERSONALIZADO
    @action(detail=True, methods=['post'])
    def calcular(self, request, pk=None):
        """
        Endpoint: POST /api/envios/rutas/{id}/calcular/
        Este endpoint gatilla el servicio de mapas para optimizar la ruta.
        """
        resultado = OptimizadorRutasService.calcular_ruta_optima(pk)
        
        if resultado['status'] == 'success':
            return Response(resultado, status=200)
        else:
            return Response(resultado, status=400)