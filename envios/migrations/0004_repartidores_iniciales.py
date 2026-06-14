from django.db import migrations


def crear_repartidores(apps, schema_editor):
    Repartidor = apps.get_model('envios', 'Repartidor')
    repartidores = [
        {'nombre_completo': 'Javier Martínez', 'rut': '11.111.111-1', 'telefono': '+56 9 1111 1111'},
        {'nombre_completo': 'Felipe Ortega', 'rut': '22.222.222-2', 'telefono': '+56 9 2222 2222'},
        {'nombre_completo': 'Juanita Pérez', 'rut': '33.333.333-3', 'telefono': '+56 9 3333 3333'},
        {'nombre_completo': 'Pepito Pérez', 'rut': '44.444.444-4', 'telefono': '+56 9 4444 4444'},
    ]
    for data in repartidores:
        Repartidor.objects.get_or_create(rut=data['rut'], defaults=data)


class Migration(migrations.Migration):

    dependencies = [
        ('envios', '0003_envio_comuna_alter_vehiculo_tipo_vehiculo'),
    ]

    operations = [
        migrations.RunPython(crear_repartidores),
    ]
