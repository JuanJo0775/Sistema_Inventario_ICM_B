from django.db import migrations

def create_default_locations(apps, schema_editor):
    Location = apps.get_model('inventory', 'Location')
    
    # Crear Vitrina
    if not Location.objects.filter(code='vitrina').exists():
        Location.objects.create(
            code='vitrina',
            name='Vitrina',
            description='Punto de venta y exhibición principal.',
            is_retail=True,
            max_capacity=100, # Valor sugerido por defecto
            is_active=True
        )
    
    # Crear Bodega
    if not Location.objects.filter(code='bodega').exists():
        Location.objects.create(
            code='bodega',
            name='Bodega',
            description='Almacén principal de mercancía.',
            is_retail=False,
            max_capacity=None, # Sin límite de capacidad
            is_active=True
        )

def remove_default_locations(apps, schema_editor):
    Location = apps.get_model('inventory', 'Location')
    Location.objects.filter(code__in=['vitrina', 'bodega']).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_location_flexible_code_and_max_capacity'),
    ]

    operations = [
        migrations.RunPython(create_default_locations, remove_default_locations),
    ]
