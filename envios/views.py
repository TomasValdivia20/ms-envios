from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from .models import Vehiculo, Repartidor, Ruta, Envio
from .services import OptimizadorRutasService, CalculadoraCostosService
from .serializers import (
    VehiculoSerializer,
    RepartidorSerializer,
    RutaSerializer,
    EnvioSerializer,
    CalcularCostosInputSerializer,
    CalcularCostosOutputSerializer,
)

class VehiculoViewSet(viewsets.ModelViewSet):
    queryset = Vehiculo.objects.all()
    serializer_class = VehiculoSerializer

class RepartidorViewSet(viewsets.ModelViewSet):
    queryset = Repartidor.objects.all()
    serializer_class = RepartidorSerializer

class EnvioViewSet(viewsets.ModelViewSet):
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer

class RutaViewSet(viewsets.ModelViewSet):
    queryset = Ruta.objects.all()
    serializer_class = RutaSerializer

    @action(detail=True, methods=['post'])
    def calcular(self, request, pk=None):
        """
        POST /api/envios/rutas/{id}/calcular/
        Optimiza la ruta con OpenRouteService.
        """
        resultado = OptimizadorRutasService.calcular_ruta_optima(pk)

        if resultado['status'] == 'success':
            return Response(resultado, status=200)
        else:
            return Response(resultado, status=400)


@api_view(['POST'])
def calcular_costos(request):
    """
    POST /api/envios/calcular-costos/
    Calcula el desglose de costos de un envío.
    """
    serializer = CalcularCostosInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    resultado = CalculadoraCostosService.calcular(serializer.validated_data)

    if 'error' in resultado:
        return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

    output_serializer = CalcularCostosOutputSerializer(data=resultado)
    if output_serializer.is_valid():
        return Response(output_serializer.validated_data, status=status.HTTP_200_OK)
    return Response(output_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
