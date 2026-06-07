import httpx
import os
from django.db import transaction
from .models import Ruta, Envio

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