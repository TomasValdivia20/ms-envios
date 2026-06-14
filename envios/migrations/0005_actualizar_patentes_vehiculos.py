from django.db import migrations


PATENTES = {
    'MOTO-01': 'KVWD-57',
    'FL-01': 'BXLP-23',
    'FM-01': 'GNRT-89',
    'CR-01': 'HMFS-41',
}


def actualizar_patentes(apps, schema_editor):
    Vehiculo = apps.get_model('envios', 'Vehiculo')
    for vieja, nueva in PATENTES.items():
        Vehiculo.objects.filter(patente=vieja).update(patente=nueva)


def revertir_patentes(apps, schema_editor):
    Vehiculo = apps.get_model('envios', 'Vehiculo')
    for nueva, vieja in {v: k for k, v in PATENTES.items()}.items():
        Vehiculo.objects.filter(patente=nueva).update(patente=vieja)


class Migration(migrations.Migration):

    dependencies = [
        ('envios', '0004_repartidores_iniciales'),
    ]

    operations = [
        migrations.RunPython(actualizar_patentes, revertir_patentes),
    ]
