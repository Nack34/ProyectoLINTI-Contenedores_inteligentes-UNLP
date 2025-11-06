from django.db import models

# Create your models here.
class Residuo(models.Model):
  id = models.AutoField(primary_key=True)
  fecha_carga = models.DateTimeField(auto_now_add=True)
  user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)
  tipo_residuo = models.ForeignKey('TipoResiduo', on_delete=models.CASCADE, null=False)

class TipoResiduo(models.Model):
  id = models.AutoField(primary_key=True)
  nombre = models.CharField(null=False, max_length=100, unique=True)
  puntos = models.IntegerField(null=False)

  class Meta:
    db_table = 'api_tipo_residuo'

class Estacion(models.Model):
  id = models.AutoField(primary_key=True)
  nombre = models.CharField(null=False, max_length=100, unique=True)
  latitud = models.FloatField(null=False)
  longitud = models.FloatField(null=False)

  class Meta:
    db_table = 'api_estacion'