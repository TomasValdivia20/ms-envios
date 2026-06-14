from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Vehiculo, Ruta, Envio
from .services import CalculadoraCostosService, OptimizadorRutasService


class CalculadoraCostosServiceTest(TestCase):
    def setUp(self):
        self.vehiculo = Vehiculo.objects.create(
            patente='ABC123',
            modelo='Honda CG',
            tipo_vehiculo='moto',
            capacidad_kg=100,
            tarifa_base=0,
            costo_por_km=Decimal('1000.00'),
            costo_por_hora=Decimal('0.00'),
            activo=True,
        )
        self.client = APIClient()

    def test_calcular_costos_exitoso_sin_instalacion(self):
        data = {
            'vehiculo_id': str(self.vehiculo.id),
            'valor_base_producto': '10000.00',
            'requiere_instalacion': False,
            'distancia_km': '10.00',
        }

        resultado = CalculadoraCostosService.calcular(data)

        self.assertEqual(resultado['vehiculo_id'], str(self.vehiculo.id))
        self.assertEqual(resultado['vehiculo_tipo'], 'Motocicleta (Carga Ligera / Express)')
        self.assertEqual(resultado['iva'], '1900.00')
        self.assertEqual(resultado['costo_transaccion'], '250.00')
        self.assertEqual(resultado['costo_logistica'], '11000.00')
        self.assertEqual(resultado['costo_instalacion'], '0')
        self.assertEqual(resultado['tiempo_estimado_min'], 20)
        self.assertEqual(resultado['total'], '23150.00')

    def test_calcular_costos_con_instalacion(self):
        data = {
            'vehiculo_id': str(self.vehiculo.id),
            'valor_base_producto': '50000.00',
            'requiere_instalacion': True,
            'distancia_km': '5.00',
        }

        resultado = CalculadoraCostosService.calcular(data)

        self.assertEqual(resultado['iva'], '9500.00')
        self.assertEqual(resultado['costo_transaccion'], '1250.00')
        self.assertEqual(resultado['costo_instalacion'], '15000')
        self.assertEqual(resultado['tiempo_estimado_min'], 10)
        self.assertEqual(resultado['total'], '81250.00')

    def test_calcular_costos_vehiculo_inactivo_devuelve_error(self):
        self.vehiculo.activo = False
        self.vehiculo.save()

        data = {
            'vehiculo_id': str(self.vehiculo.id),
            'valor_base_producto': '10000.00',
            'requiere_instalacion': False,
            'distancia_km': '1.00',
        }

        resultado = CalculadoraCostosService.calcular(data)
        self.assertIn('error', resultado)
        self.assertEqual(resultado['error'], 'El vehículo no está activo')

    def test_calcular_costos_endpoint_post(self):
        url = reverse('calcular-costos')
        response = self.client.post(url, data={
            'vehiculo_id': str(self.vehiculo.id),
            'valor_base_producto': '10000.00',
            'requiere_instalacion': False,
            'distancia_km': '10.00',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], Decimal('23150.00'))


class OptimizadorRutasServiceTest(TestCase):
    def setUp(self):
        self.ruta = Ruta.objects.create()
        self.envio1 = Envio.objects.create(
            codigo_seguimiento='ENVIO1',
            referencia_externa_id='REF1',
            valor_base_producto=Decimal('10000.00'),
            requiere_instalacion=False,
            direccion_destino='Av. Siempre Viva 123',
            latitud=Decimal('-33.45'),
            longitud=Decimal('-70.65'),
            ruta=self.ruta,
        )
        self.envio2 = Envio.objects.create(
            codigo_seguimiento='ENVIO2',
            referencia_externa_id='REF2',
            valor_base_producto=Decimal('8000.00'),
            requiere_instalacion=False,
            direccion_destino='Av. Providencia 456',
            latitud=Decimal('-33.44'),
            longitud=Decimal('-70.66'),
            ruta=self.ruta,
        )

    def test_calcular_ruta_simulada_actualiza_ruta_y_envios(self):
        resultado = OptimizadorRutasService.calcular_ruta_optima(self.ruta.id)

        self.assertEqual(resultado['status'], 'success')

        self.ruta.refresh_from_db()
        self.envio1.refresh_from_db()
        self.envio2.refresh_from_db()

        self.assertEqual(self.ruta.estado, 'En_Transito')
        self.assertEqual(self.ruta.distancia_total_km, Decimal('12.50'))
        self.assertEqual(self.ruta.tiempo_estimado_min, 35)
        self.assertEqual(self.envio1.orden_parada, 1)
        self.assertEqual(self.envio1.estado, 'En_Camino')
        self.assertEqual(self.envio2.orden_parada, 2)
        self.assertEqual(self.envio2.estado, 'En_Camino')

    def test_calcular_ruta_sin_envios_devuelve_error(self):
        ruta_vacia = Ruta.objects.create()
        resultado = OptimizadorRutasService.calcular_ruta_optima(ruta_vacia.id)

        self.assertEqual(resultado['status'], 'error')
        self.assertIn('La ruta no tiene envíos asignados', resultado['mensaje'])
