import httpx
import math
import os
import re
from decimal import Decimal
from django.db import transaction
from .models import Ruta, Envio, Vehiculo


BODEGA_CENTRAL_LAT = Decimal('-33.4372')
BODEGA_CENTRAL_LNG = Decimal('-70.6506')


class GeocodificadorService:
    @staticmethod
    def geocodificar(direccion):
        api_key = os.environ.get('MAPBOX_TOKEN', 'MOCK_KEY_LOCAL')

        if api_key == 'MOCK_KEY_LOCAL':
            return GeocodificadorService._simular(direccion)

        url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/{}.json'.format(
            re.sub(r'[^\w\s,.-]', '', direccion)
        )
        params = {'access_token': api_key, 'country': 'CL', 'limit': 1}

        try:
            response = httpx.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('features'):
                feature = data['features'][0]
                lng, lat = feature['center']
                comuna = GeocodificadorService._extraer_comuna(feature)
                return {
                    'latitud': Decimal(str(lat)),
                    'longitud': Decimal(str(lng)),
                    'comuna': comuna,
                }
        except Exception:
            pass

        return GeocodificadorService._simular(direccion)

    @staticmethod
    def _simular(direccion):
        import hashlib
        seed = int(hashlib.md5(direccion.encode()).hexdigest()[:8], 16)
        lat = Decimal(str(round(-33.4 + (seed % 100) / 1000, 6)))
        lng = Decimal(str(round(-70.6 + (seed % 100) / 1000, 6)))
        partes = [p.strip() for p in direccion.split(',')]
        comuna = partes[-1] if len(partes) > 1 else None
        return {
            'latitud': lat,
            'longitud': lng,
            'comuna': comuna,
        }

    @staticmethod
    def _extraer_comuna(feature):
        context = feature.get('context', [])
        for item in context:
            if 'place' in item.get('id', ''):
                return item['text']
        partes = feature.get('place_name', '').split(',')
        return partes[-1].strip() if len(partes) > 1 else None

class OptimizadorRutasService:
    @staticmethod
    def calcular_ruta_optima(ruta_id):
        try:
            # 1. Obtener la ruta y los envíos asignados a ella
            ruta = Ruta.objects.get(id=ruta_id)
            envios = ruta.paradas.all()
            
            if envios.count() == 0:
                raise ValueError("La ruta no tiene envíos asignados.")

            # 2. Preparar coordenadas (OpenRouteService usa [Longitud, Latitud])
            coordenadas = []
            # Punto de partida fijo: La Bodega Central (Ej: Santiago Centro)
            coordenadas.append([-70.6506, -33.4372]) 
            
            for envio in envios:
                coordenadas.append([float(envio.longitud), float(envio.latitud)])

            # 3. Llamada asíncrona/HTTP a OpenRouteService
            api_key = os.environ.get('ORS_API_KEY', 'MOCK_KEY_LOCAL')
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            
            # SI NO HAY API KEY, usamos el simulador para que no se rompa tu entorno local
            if api_key == 'MOCK_KEY_LOCAL':
                return OptimizadorRutasService._simulador_local_modo_desarrollo(ruta, envios)

            headers = {
                'Authorization': api_key,
                'Content-Type': 'application/json'
            }
            payload = {
                "coordinates": coordenadas,
                "format": "geojson"
            }

            # Usamos httpx (No requests) para mayor eficiencia
            response = httpx.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # 4. Extraer datos (Distancia, Tiempo, y el Polígono del mapa)
            propiedades = data['features'][0]['properties']
            distancia_km = propiedades['segments'][0]['distance'] / 1000
            tiempo_min = propiedades['segments'][0]['duration'] / 60
            geometria = data['features'][0]['geometry'] # Esto es lo que leerá Leaflet.js

            # 5. Guardar en Base de Datos de forma segura usando Transacciones atómicas
            with transaction.atomic():
                ruta.distancia_total_km = round(distancia_km, 2)
                ruta.tiempo_estimado_min = int(tiempo_min)
                ruta.geometria_ruta = str(geometria)
                ruta.estado = 'En_Transito'
                ruta.save()

                # Actualizamos los envíos para indicar que ya salieron de bodega
                for index, envio in enumerate(envios, start=1):
                    envio.orden_parada = index
                    envio.estado = 'En_Camino'
                    envio.save()

            return {"status": "success", "mensaje": "Ruta real calculada con OpenRouteService"}

        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    @staticmethod
    def _simulador_local_modo_desarrollo(ruta, envios):
        """
        Fallback simulado: Si no tienes internet o la API Key, esto crea 
        datos falsos realistas para que el Frontend pueda seguir trabajando.
        """
        with transaction.atomic():
            ruta.distancia_total_km = 12.5
            ruta.tiempo_estimado_min = 35
            # Un pequeño polígono de prueba en Santiago para Leaflet
            ruta.geometria_ruta = '{"coordinates": [[-70.65, -33.43], [-70.66, -33.45]], "type": "LineString"}'
            ruta.estado = 'En_Transito'
            ruta.save()
            
            for index, envio in enumerate(envios, start=1):
                envio.orden_parada = index
                envio.estado = 'En_Camino'
                envio.save()
                
        return {"status": "success", "mensaje": "Ruta simulada (Modo Local MOCK) calculada con éxito."}

    @staticmethod
    def completar_ruta(ruta_id):
        try:
            ruta = Ruta.objects.get(id=ruta_id)
            if ruta.estado != 'En_Transito':
                return {'status': 'error', 'mensaje': 'La ruta no está en tránsito'}

            from django.utils import timezone
            with transaction.atomic():
                ruta.estado = 'Completada'
                ruta.fecha_completada = timezone.now()
                ruta.save()

                ruta.paradas.all().update(estado='Entregado')

            return {'status': 'success', 'mensaje': 'Ruta completada exitosamente'}
        except Ruta.DoesNotExist:
            return {'status': 'error', 'mensaje': 'Ruta no encontrada'}
        except Exception as e:
            return {'status': 'error', 'mensaje': str(e)}


class CalculadoraCostosService:
    IVA = Decimal('0.19')
    TASA_TRANSACCION = Decimal('0.025')
    VELOCIDAD_PROMEDIO_KMPH = Decimal('30')
    COSTO_INSTALACION = Decimal('15000')

    @staticmethod
    def distancia_ortodromica(lat1, lng1, lat2, lng2):
        R = Decimal('6371')
        d_lat = math.radians(float(lat2 - lat1))
        d_lng = math.radians(float(lng2 - lng1))
        a = (math.sin(d_lat / 2) ** 2 +
             math.cos(math.radians(float(lat1))) *
             math.cos(math.radians(float(lat2))) *
             math.sin(d_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return Decimal(str(round(R * Decimal(str(c)), 2)))

    @staticmethod
    def calcular_pago_por_hora(vehiculo):
        if vehiculo.tipo_vehiculo == 'moto':
            return Decimal('3000')
        elif vehiculo.tipo_vehiculo == 'furgon_ligero':
            return Decimal('5000')
        elif vehiculo.tipo_vehiculo == 'furgon_mediano':
            return Decimal('7000')
        else:
            return Decimal('9000')

    @staticmethod
    def calcular(data):
        try:
            vehiculo = Vehiculo.objects.get(id=data['vehiculo_id'])
            if not vehiculo.activo:
                raise ValueError("El vehículo no está activo")

            valor_base = Decimal(str(data['valor_base_producto']))
            requiere_instalacion = data.get('requiere_instalacion', False)

            direccion_destino = data.get('direccion_destino')
            if direccion_destino:
                geo = GeocodificadorService.geocodificar(direccion_destino)
                distancia_km = CalculadoraCostosService.distancia_ortodromica(
                    BODEGA_CENTRAL_LAT, BODEGA_CENTRAL_LNG,
                    geo['latitud'], geo['longitud'],
                )
            else:
                distancia_km = Decimal(str(data.get('distancia_km', 0)))

            iva = (valor_base * CalculadoraCostosService.IVA).quantize(Decimal('0.01'))
            costo_transaccion = (valor_base * CalculadoraCostosService.TASA_TRANSACCION).quantize(Decimal('0.01'))
            costo_logistica = (vehiculo.costo_por_km * distancia_km).quantize(Decimal('0.01'))

            if distancia_km > 0:
                tiempo_min = int((distancia_km / CalculadoraCostosService.VELOCIDAD_PROMEDIO_KMPH) * 60)
            else:
                tiempo_min = 0

            pago_hora = CalculadoraCostosService.calcular_pago_por_hora(vehiculo)
            costo_operador = (pago_hora * (Decimal(str(tiempo_min)) / Decimal('60'))).quantize(Decimal('0.01'))

            costo_logistica_total = (costo_logistica + costo_operador).quantize(Decimal('0.01'))

            costo_instalacion = CalculadoraCostosService.COSTO_INSTALACION if requiere_instalacion else Decimal('0')

            total = (valor_base + iva + costo_transaccion + costo_logistica_total + costo_instalacion).quantize(Decimal('0.01'))

            return {
                'vehiculo_id': str(vehiculo.id),
                'vehiculo_tipo': vehiculo.get_tipo_vehiculo_display(),
                'valor_base': str(valor_base),
                'iva': str(iva),
                'costo_transaccion': str(costo_transaccion),
                'costo_logistica': str(costo_logistica_total),
                'costo_instalacion': str(costo_instalacion),
                'tiempo_estimado_min': tiempo_min,
                'total': str(total),
            }

        except Vehiculo.DoesNotExist:
            return {'error': 'Vehículo no encontrado'}
        except Exception as e:
            return {'error': str(e)}