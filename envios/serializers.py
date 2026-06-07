from rest_framework import serializers
from .models import Vehiculo, Repartidor, Ruta, Envio

class VehiculoSerializer(serializers.ModelSerializer):
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

# Serializer para mostrar los envíos DENTRO de una ruta
class EnvioEnRutaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envio
        # Solo mandamos lo esencial al mapa para no saturar la red
        fields = ['id', 'codigo_seguimiento', 'direccion_destino', 'latitud', 'longitud', 'orden_parada', 'estado']

class RutaSerializer(serializers.ModelSerializer):
    # TRUCO 1: "Aplanar" datos. En vez de devolver solo el ID "uuid-...", 
    # le mandamos al frontend directamente el nombre del repartidor y la patente.
    repartidor_nombre = serializers.CharField(source='repartidor.nombre_completo', read_only=True)
    vehiculo_patente = serializers.CharField(source='vehiculo.patente', read_only=True)
    
    # TRUCO 2: Serializador Anidado. Como en el modelo Envio le pusimos related_name='paradas',
    # DRF automáticamente buscará todos los envíos de esta ruta y los meterá en una lista JSON.
    paradas = EnvioEnRutaSerializer(many=True, read_only=True)

    class Meta:
        model = Ruta
        fields = [
            'id', 'repartidor', 'repartidor_nombre', 'vehiculo', 'vehiculo_patente',
            'estado', 'distancia_total_km', 'tiempo_estimado_min', 'geometria_ruta',
            'fecha_creacion', 'fecha_completada', 'paradas'
        ]