from rest_framework import serializers
from .models import Vehiculo, Repartidor, Ruta, Envio

class VehiculoSerializer(serializers.ModelSerializer):
    tipo_vehiculo_display = serializers.CharField(source='get_tipo_vehiculo_display', read_only=True)

    class Meta:
        model = Vehiculo
        fields = '__all__'

class RepartidorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repartidor
        fields = '__all__'

class EnvioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        fields = '__all__'

class EnvioEnRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        fields = ['id', 'codigo_seguimiento', 'direccion_destino', 'latitud', 'longitud', 'orden_parada', 'estado']

class RutaSerializer(serializers.ModelSerializer):
    repartidor_nombre = serializers.CharField(source='repartidor.nombre_completo', read_only=True)
    vehiculo_patente = serializers.CharField(source='vehiculo.patente', read_only=True)
    paradas = EnvioEnRutaSerializer(many=True, read_only=True)

    class Meta:
        model = Ruta
        fields = [
            'id', 'repartidor', 'repartidor_nombre', 'vehiculo', 'vehiculo_patente',
            'estado', 'distancia_total_km', 'tiempo_estimado_min', 'geometria_ruta',
            'fecha_creacion', 'fecha_completada', 'paradas'
        ]

class CalcularCostosInputSerializer(serializers.Serializer):
    vehiculo_id = serializers.UUIDField()
    valor_base_producto = serializers.DecimalField(max_digits=12, decimal_places=2)
    requiere_instalacion = serializers.BooleanField(default=False)
    distancia_km = serializers.DecimalField(max_digits=8, decimal_places=2, default=0)

class CalcularCostosOutputSerializer(serializers.Serializer):
    vehiculo_id = serializers.UUIDField()
    vehiculo_tipo = serializers.CharField()
    valor_base = serializers.DecimalField(max_digits=12, decimal_places=2)
    iva = serializers.DecimalField(max_digits=12, decimal_places=2)
    costo_transaccion = serializers.DecimalField(max_digits=12, decimal_places=2)
    costo_logistica = serializers.DecimalField(max_digits=12, decimal_places=2)
    costo_instalacion = serializers.DecimalField(max_digits=12, decimal_places=2)
    tiempo_estimado_min = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
