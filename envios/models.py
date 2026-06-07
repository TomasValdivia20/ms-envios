import uuid
from django.db import models

class Vehiculo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patente = models.CharField(max_length=10, unique=True)
    modelo = models.CharField(max_length=50)
    capacidad_kg = models.DecimalField(max_digits=7, decimal_places=2)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.patente} - {self.modelo}"

class Repartidor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rut = models.CharField(max_length=12, unique=True) # Formato chileno
    nombre_completo = models.CharField(max_length=150)
    telefono = models.CharField(max_length=15)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre_completo

class Ruta(models.Model):
    ESTADOS_RUTA = (
        ('Planificacion', 'En Planificación'),
        ('En_Transito', 'En Tránsito'),
        ('Completada', 'Completada'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repartidor = models.ForeignKey(Repartidor, on_delete=models.SET_NULL, null=True, blank=True)
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RUTA, default='Planificacion')
    
    # Datos que calcularemos con la API de OpenRouteService
    distancia_total_km = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    tiempo_estimado_min = models.IntegerField(null=True, blank=True)
    
    # Guardaremos el polígono de la ruta codificado (Polyline) para dibujarlo rápido en el Frontend con Leaflet
    geometria_ruta = models.TextField(null=True, blank=True) 
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_completada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ruta {self.id} - {self.estado}"

class Envio(models.Model):
    ESTADOS_ENVIO = (
        ('Bodega', 'En Bodega'),
        ('Asignado', 'Asignado a Ruta'),
        ('En_Camino', 'En Camino'),
        ('Entregado', 'Entregado'),
        ('Fallido', 'Intento Fallido'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo_seguimiento = models.CharField(max_length=20, unique=True)
    
    # ID del producto o pedido que viene del ms-inventario/ms-pedidos
    referencia_externa_id = models.CharField(max_length=100) 
    
    # Ubicación exacta para la API de mapas
    direccion_destino = models.CharField(max_length=255)
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Relación con la Ruta de despacho
    ruta = models.ForeignKey(Ruta, related_name='paradas', on_delete=models.SET_NULL, null=True, blank=True)
    
    # El algoritmo del backend llenará este campo (ej: parada 1, parada 2, parada 3)
    orden_parada = models.IntegerField(null=True, blank=True) 
    
    estado = models.CharField(max_length=20, choices=ESTADOS_ENVIO, default='Bodega')
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Envío {self.codigo_seguimiento} - {self.estado}"