from django.db import migrations

def poblar_tipos(apps, schema_editor):
    """
    Puebla la tabla TipoResiduo con los 6 tipos básicos.
    """
    # Obtenemos el modelo 'TipoResiduo' de la app 'api'
    TipoResiduo = apps.get_model('api', 'TipoResiduo')
    
    tipos_con_puntos = [
        ('Carton', 10),
        ('Vidrio', 15),
        ('Metal', 20),
        ('Papel', 10),
        ('Plastico', 15),
        ('Basura', 0)
    ]
    
    for nombre, puntos in tipos_con_puntos:
        TipoResiduo.objects.create(nombre=nombre, puntos=puntos)

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(poblar_tipos),
    ]